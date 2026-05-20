import asyncio
from collections import defaultdict
from collections.abc import AsyncIterable
from shutil import copyfileobj
from uuid import UUID, uuid4

import orjson
import sqlalchemy
import sqlalchemy.exc
from fastapi import (
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    Request,
    status,
)
from fastapi.datastructures import UploadFile
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import UUID4, BaseModel, Field
from slugify import slugify

from mealie.core import exceptions
from mealie.core.dependencies import (
    get_temporary_zip_path,
)
from mealie.pkgs import cache
from mealie.repos.all_repositories import get_repositories
from mealie.routes._base import controller
from mealie.routes._base.routers import MealieCrudRoute, UserAPIRouter
from mealie.schema.cookbook.cookbook import ReadCookBook
from mealie.schema.make_dependable import make_dependable
from mealie.schema.openai import OpenAIRecipe
from mealie.schema.openai.recipe import OpenAIRecipeIngredient, OpenAIRecipeInstructionTimerResult
from mealie.schema.openai.recipe_ingredient import OpenAIIngredient
from mealie.schema.recipe import (
    IngredientConfidence,
    IngredientReferences,
    Recipe,
    ScrapeRecipe,
    ScrapeRecipeData,
)
from mealie.schema.recipe.recipe import (
    CreateRecipe,
    CreateRecipeByUrlBulk,
    RecipeLastMade,
    RecipeSummary,
)
from mealie.schema.recipe.recipe_asset import RecipeAsset
from mealie.schema.recipe.recipe_scraper import ScrapeRecipeTest
from mealie.schema.recipe.recipe_suggestion import RecipeSuggestionQuery, RecipeSuggestionResponse
from mealie.schema.recipe.recipe_timer import RecipeTimer
from mealie.schema.recipe.request_helpers import (
    RecipeDuplicate,
    UpdateImageResponse,
)
from mealie.schema.response import PaginationBase, PaginationQuery
from mealie.schema.response.pagination import RecipeSearchQuery
from mealie.schema.response.responses import (
    ErrorResponse,
    SSEDataEventDone,
    SSEDataEventMessage,
    SSEDataEventStatus,
    SuccessResponse,
)
from mealie.services import urls
from mealie.services.event_bus_service.event_types import (
    EventOperation,
    EventRecipeBulkData,
    EventRecipeBulkReportData,
    EventRecipeData,
    EventTypes,
)
from mealie.services.openai import OpenAIDataInjection, OpenAIService
from mealie.services.parser_services._base import DataMatcher
from mealie.services.parser_services.openai.parser import OpenAIParser
from mealie.services.parser_services.parser_utils.duration_parser import DurationParser
from mealie.services.recipe.recipe_data_service import (
    InvalidDomainError,
    NotAnImageError,
    RecipeDataService,
)
from mealie.services.scraper.recipe_bulk_scraper import RecipeBulkScraperService
from mealie.services.scraper.scraped_extras import ScraperContext
from mealie.services.scraper.scraper import create_from_html
from mealie.services.scraper.scraper_strategies import (
    ForceTimeoutException,
    RecipeScraperOpenAI,
    RecipeScraperPackage,
)

from ._base import BaseRecipeController, JSONBytes

ASSET_ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "gif", "webp", "bmp", "avif", "txt", "md", "csv", "json"}

router = UserAPIRouter(prefix="/recipes", route_class=MealieCrudRoute)


class ParseInstructionTimersStepIn(BaseModel):
    index: int
    text: str


class ParseInstructionTimersIn(BaseModel):
    steps: list[ParseInstructionTimersStepIn]


class ParseInstructionTimersStepOut(BaseModel):
    index: int
    timers: list[RecipeTimer]


class ParseInstructionTimersOut(BaseModel):
    steps: list[ParseInstructionTimersStepOut]


class ParseRecipeWithAIIngredientIn(BaseModel):
    display: str | None = None
    reference_id: UUID | None = Field(None, alias="referenceId")


class ParseRecipeWithAIStepIn(BaseModel):
    id: UUID | None = None
    text: str = ""
    ingredient_references: list[IngredientReferences] = Field(default_factory=list, alias="ingredientReferences")


class ParseRecipeWithAIIn(BaseModel):
    recipe_ingredient: list[ParseRecipeWithAIIngredientIn] = Field(default_factory=list, alias="recipeIngredient")
    recipe_instructions: list[ParseRecipeWithAIStepIn] = Field(default_factory=list, alias="recipeInstructions")
    org_url: str | None = Field(None, alias="orgURL")


class ParseRecipeWithAINamedItem(BaseModel):
    id: UUID | None = None
    name: str


class ParseRecipeWithAIIngredientWithQuantityOut(BaseModel):
    model_config = {"populate_by_name": True}

    reference_id: UUID | None = Field(None, alias="referenceId")
    quantity: float | None = None
    quantity_in_ml: float | None = Field(None, alias="quantityInMl")
    unit_name: str | None = Field(None, alias="unitName")
    comment: str | None = None


class ParseRecipeWithAIIngredientItemOut(BaseModel):
    model_config = {"populate_by_name": True}

    reference_id: UUID | None = Field(None, alias="referenceId")
    display: str | None = None
    confidence: IngredientConfidence | None = None
    quantity: float | None = None
    unit: ParseRecipeWithAINamedItem | None = None
    food: ParseRecipeWithAINamedItem | None = None
    note: str | None = None
    quantity_in_ml: float | None = Field(None, alias="quantityInMl")


class ParseRecipeWithAIStepItemOut(BaseModel):
    model_config = {"populate_by_name": True}

    id: UUID | None = None
    title: str | None = None
    text: str
    ingredient_references: list[IngredientReferences] = Field(default_factory=list, alias="ingredientReferences")
    timers: list[RecipeTimer] = Field(default_factory=list)
    preparation_instruction_id: UUID | None = Field(None, alias="preparationInstructionId")
    ingredients_with_quantity: list[ParseRecipeWithAIIngredientWithQuantityOut] = Field(
        default_factory=list, alias="ingredientsWithQuantity"
    )


class ParseRecipeWithAIOut(BaseModel):
    model_config = {"populate_by_name": True}

    recipe_ingredient: list[ParseRecipeWithAIIngredientItemOut] = Field(default_factory=list, alias="recipeIngredient")
    recipe_instructions: list[ParseRecipeWithAIStepItemOut] = Field(default_factory=list, alias="recipeInstructions")
    org_url: str | None = Field(None, alias="orgURL")
    primary_unit_system: str | None = Field(None, alias="primaryUnitSystem")


class ParseRecipeInstructionsWithAIStepIn(BaseModel):
    id: UUID | None = None
    text: str = ""
    timers: list[RecipeTimer] = Field(default_factory=list)


class ParseRecipeInstructionsWithAIIn(BaseModel):
    primary_unit_system: str | None = Field(None, alias="primaryUnitSystem")
    org_url: str | None = Field(None, alias="orgURL")
    instructions: list[ParseRecipeInstructionsWithAIStepIn] = Field(default_factory=list)


class ParseRecipeInstructionsWithAIStepOut(BaseModel):
    model_config = {"populate_by_name": True}

    id: UUID | None = None
    text: str
    timers: list[RecipeTimer] = Field(default_factory=list)


class ParseRecipeInstructionsWithAIOut(BaseModel):
    instructions: list[ParseRecipeInstructionsWithAIStepOut] = Field(default_factory=list)


@controller(router)
class RecipeController(BaseRecipeController):
    def _get_parse_recipe_with_ai_prompt(self, openai_service: OpenAIService) -> str:
        if openai_service.send_db_data:
            data_matcher = DataMatcher(self.repos)
            unit_aliases = list(set(data_matcher.units_by_alias))
            if unit_aliases:
                return openai_service.get_prompt(
                    "recipes.parse-recipe-editor",
                    data_injections=[
                        OpenAIDataInjection(
                            description=(
                                "Below is a list of unit names and abbreviations from the user's database. "
                                "Use this as the preferred unit vocabulary when parsing ingredients and "
                                "instruction quantities."
                            ),
                            value=unit_aliases,
                        )
                    ],
                )

        return openai_service.get_prompt("recipes.parse-recipe-editor")

    @staticmethod
    def _get_parse_instruction_timers_with_ai_prompt(openai_service: OpenAIService) -> str:
        return openai_service.get_prompt("recipes.parse-recipe-instruction-timers")

    @staticmethod
    def _parse_uuid(value: str | None) -> UUID | None:
        if not value:
            return None

        try:
            return UUID(value)
        except ValueError:
            return None

    def _build_parse_recipe_with_ai_ingredient_out(
        self,
        ingredient_parser: OpenAIParser,
        data: ParseRecipeWithAIIn,
        index: int,
        ai_ingredient: OpenAIRecipeIngredient,
        reference_id: UUID,
    ) -> ParseRecipeWithAIIngredientItemOut:
        original_text = (
            data.recipe_ingredient[index].display if index < len(data.recipe_ingredient) else ai_ingredient.text
        )
        parsed_ingredient = ingredient_parser.convert_ingredient(
            original_text or ai_ingredient.text,
            OpenAIIngredient(
                quantity=ai_ingredient.quantity,
                unit=ai_ingredient.unit_name,
                food=ai_ingredient.food_name,
                note=ai_ingredient.note,
            ),
        )

        return ParseRecipeWithAIIngredientItemOut(
            reference_id=reference_id,
            display=ai_ingredient.text,
            confidence=parsed_ingredient.confidence,
            quantity=parsed_ingredient.ingredient.quantity,
            unit=(
                ParseRecipeWithAINamedItem(
                    id=parsed_ingredient.ingredient.unit.id,
                    name=parsed_ingredient.ingredient.unit.name,
                )
                if parsed_ingredient.ingredient.unit and parsed_ingredient.ingredient.unit.name
                else None
            ),
            food=(
                ParseRecipeWithAINamedItem(
                    id=parsed_ingredient.ingredient.food.id,
                    name=parsed_ingredient.ingredient.food.name,
                )
                if parsed_ingredient.ingredient.food and parsed_ingredient.ingredient.food.name
                else None
            ),
            note=parsed_ingredient.ingredient.note,
            quantity_in_ml=ai_ingredient.quantity_in_ml,
        )

    @staticmethod
    def _resolve_unique_uuid(preferred: UUID | None, fallback: UUID | None, seen: set[UUID]) -> UUID:
        if preferred and preferred not in seen:
            seen.add(preferred)
            return preferred

        if fallback and fallback not in seen:
            seen.add(fallback)
            return fallback

        new_id = uuid4()
        while new_id in seen:
            new_id = uuid4()

        seen.add(new_id)
        return new_id

    def handle_exceptions(self, ex: Exception) -> None:
        thrownType = type(ex)

        if thrownType == exceptions.PermissionDenied:
            self.logger.error("Permission Denied on recipe controller action")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=ErrorResponse.respond(message="Permission Denied")
            )
        elif thrownType == exceptions.NoEntryFound:
            self.logger.error("No Entry Found on recipe controller action")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=ErrorResponse.respond(message="No Entry Found")
            )
        elif thrownType == sqlalchemy.exc.IntegrityError:
            self.logger.error("SQL Integrity Error on recipe controller action")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorResponse.respond(message="Recipe already exists")
            )
        elif thrownType == exceptions.RecursiveRecipe:
            self.logger.error("Recursive Recipe Link Error on recipe controller action")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.respond(message=self.t("exceptions.recursive-recipe-link")),
            )
        elif thrownType == exceptions.SlugError:
            self.logger.error("Failed to generate a valid slug from recipe name")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.respond(message="Unable to generate recipe slug"),
            )
        else:
            self.logger.error("Unknown Error on recipe controller action")
            self.logger.exception(ex)
            raise HTTPException(
                status_code=500, detail=ErrorResponse.respond(message="Unknown Error", exception=ex.__class__.__name__)
            )

    # =======================================================================
    # URL Scraping Operations

    @router.post("/test-scrape-url")
    async def test_parse_recipe_url(self, data: ScrapeRecipeTest):
        # Debugger should produce the same result as the scraper sees before cleaning
        ScraperClass = RecipeScraperOpenAI if data.use_openai else RecipeScraperPackage
        try:
            if scraped_data := await ScraperClass(data.url, self.translator).scrape_url():
                return scraped_data.schema.data
        except ForceTimeoutException as e:
            raise HTTPException(
                status_code=408, detail=ErrorResponse.respond(message="Recipe Scraping Timed Out")
            ) from e

        return "recipe_scrapers was unable to scrape this URL"

    @router.post("/create/html-or-json", status_code=201, response_model=str)
    async def create_recipe_from_html_or_json(self, req: ScrapeRecipeData) -> str:
        """Takes in raw HTML or a https://schema.org/Recipe object as a JSON string and parses it like a URL"""

        if req.data.startswith("{"):
            req.data = RecipeScraperPackage.ld_json_to_html(req.data)

        async for event in self._create_recipe_from_web(req):
            if isinstance(event.data, SSEDataEventDone):
                return event.data.slug
            if isinstance(event.data, SSEDataEventMessage) and event.event == SSEDataEventStatus.ERROR:
                raise HTTPException(status_code=400, detail=ErrorResponse.respond(message=event.data.message))

        # This should never be reachable, since we should always hit DONE or hit an exception/ERROR
        raise HTTPException(status_code=500, detail=ErrorResponse.respond(message="Unknown Error"))

    @router.post("/create/html-or-json/stream", response_class=EventSourceResponse)
    async def create_recipe_from_html_or_json_stream(self, req: ScrapeRecipeData) -> AsyncIterable[ServerSentEvent]:
        """
        Takes in raw HTML or a https://schema.org/Recipe object as a JSON string and parses it like a URL,
        streaming progress via SSE
        """

        if req.data.startswith("{"):
            req.data = RecipeScraperPackage.ld_json_to_html(req.data)

        async for event in self._create_recipe_from_web(req):
            yield event

    @router.post("/create/url", status_code=201, response_model=str)
    async def parse_recipe_url(self, req: ScrapeRecipe) -> str:
        """Takes in a URL and attempts to scrape data and load it into the database"""

        async for event in self._create_recipe_from_web(req):
            if isinstance(event.data, SSEDataEventDone):
                return event.data.slug
            if isinstance(event.data, SSEDataEventMessage) and event.event == SSEDataEventStatus.ERROR:
                raise HTTPException(status_code=400, detail=ErrorResponse.respond(message=event.data.message))

        # This should never be reachable, since we should always hit DONE or hit an exception/ERROR
        raise HTTPException(status_code=500, detail=ErrorResponse.respond(message="Unknown Error"))

    @router.post("/create/url/stream", response_class=EventSourceResponse)
    async def parse_recipe_url_stream(self, req: ScrapeRecipe) -> AsyncIterable[ServerSentEvent]:
        """
        Takes in a URL and attempts to scrape data and load it into the database,
        streaming progress via SSE
        """

        async for event in self._create_recipe_from_web(req):
            yield event

    async def _create_recipe_from_web(self, req: ScrapeRecipe | ScrapeRecipeData) -> AsyncIterable[ServerSentEvent]:
        """
        Create a recipe from the web, returning progress via SSE.
        Events will continue to be yielded until:
            - The recipe is created, emitting:
                - event=SSEDataEventStatus.DONE
                - data=SSEDataEventDone(...)
            - An exception is raised, emitting:
                - event=SSEDataEventStatus.ERROR
                - data=SSEDataEventMessage(...)
        """

        if isinstance(req, ScrapeRecipeData):
            html = req.data
            url = req.url or ""
        else:
            html = None
            url = req.url

        queue: asyncio.Queue[ServerSentEvent | None] = asyncio.Queue()

        async def on_progress(message: str) -> None:
            await queue.put(
                ServerSentEvent(
                    data=SSEDataEventMessage(message=message),
                    event=SSEDataEventStatus.PROGRESS,
                )
            )

        async def run() -> None:
            try:
                recipe, extras = await create_from_html(url, self.translator, html, on_progress=on_progress)
                slug = self._finish_recipe_from_web(req, recipe, extras)
                await queue.put(
                    ServerSentEvent(
                        data=SSEDataEventDone(slug=slug),
                        event=SSEDataEventStatus.DONE,
                    )
                )
            except Exception as e:
                self.logger.exception("Error in streaming recipe creation")
                await queue.put(
                    ServerSentEvent(
                        data=SSEDataEventMessage(message=e.__class__.__name__),
                        event=SSEDataEventStatus.ERROR,
                    )
                )
            finally:
                await queue.put(None)

        asyncio.create_task(run())
        while (event := await queue.get()) is not None:
            yield event

    def _finish_recipe_from_web(self, req: ScrapeRecipe | ScrapeRecipeData, recipe: Recipe, extras: object) -> str:
        if req.include_tags:
            ctx = ScraperContext(self.repos)
            recipe.tags = extras.use_tags(ctx)  # type: ignore

        if req.include_categories:
            ctx = ScraperContext(self.repos)
            recipe.recipe_category = extras.use_categories(ctx)  # type: ignore

        new_recipe = self.service.create_one(recipe)

        if new_recipe:
            self.publish_event(
                event_type=EventTypes.recipe_created,
                document_data=EventRecipeData(operation=EventOperation.create, recipe_slug=new_recipe.slug),
                group_id=new_recipe.group_id,
                household_id=new_recipe.household_id,
                message=self.t(
                    "notifications.generic-created-with-url",
                    name=new_recipe.name,
                    url=urls.recipe_url(self.group.slug, new_recipe.slug, self.settings.BASE_URL),
                ),
            )

        return new_recipe.slug

    @router.post("/create/url/bulk", status_code=202)
    def parse_recipe_url_bulk(self, bulk: CreateRecipeByUrlBulk, bg_tasks: BackgroundTasks):
        """Takes in a URL and attempts to scrape data and load it into the database"""
        bulk_scraper = RecipeBulkScraperService(self.service, self.repos, self.group, self.translator)
        report_id = bulk_scraper.get_report_id()
        bg_tasks.add_task(bulk_scraper.scrape, bulk)

        self.publish_event(
            event_type=EventTypes.recipe_created,
            document_data=EventRecipeBulkReportData(operation=EventOperation.create, report_id=report_id),
            group_id=self.group_id,
            household_id=self.household_id,
        )

        return {"reportId": report_id}

    # ==================================================================================================================
    # Other Create Operations

    @router.post("/create/zip", status_code=201)
    def create_recipe_from_zip(self, archive: UploadFile = File(...)):
        """Create recipe from archive"""
        with get_temporary_zip_path() as temp_path:
            recipe = self.service.create_from_zip(archive, temp_path)
            self.publish_event(
                event_type=EventTypes.recipe_created,
                document_data=EventRecipeData(operation=EventOperation.create, recipe_slug=recipe.slug),
                group_id=recipe.group_id,
                household_id=recipe.household_id,
            )

        return recipe.slug

    @router.post("/create/image", status_code=201)
    async def create_recipe_from_image(
        self,
        images: list[UploadFile] = File(...),
        translate_language: str | None = Query(None, alias="translateLanguage"),
    ):
        """
        Create a recipe from an image using OpenAI.
        Optionally specify a language for it to translate the recipe to.
        """

        if not (self.settings.OPENAI_ENABLED and self.settings.OPENAI_ENABLE_IMAGE_SERVICES):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse.respond("OpenAI image services are not enabled"),
            )

        recipe = await self.service.create_from_images(images, translate_language)
        self.publish_event(
            event_type=EventTypes.recipe_created,
            document_data=EventRecipeData(operation=EventOperation.create, recipe_slug=recipe.slug),
            group_id=recipe.group_id,
            household_id=recipe.household_id,
        )

        return recipe.slug

    # ==================================================================================================================
    # CRUD Operations

    @router.get("", response_model=PaginationBase[RecipeSummary])
    def get_all(
        self,
        request: Request,
        q: PaginationQuery = Depends(make_dependable(PaginationQuery)),
        search_query: RecipeSearchQuery = Depends(make_dependable(RecipeSearchQuery)),
        categories: list[UUID4 | str] | None = Query(None),
        tags: list[UUID4 | str] | None = Query(None),
        tools: list[UUID4 | str] | None = Query(None),
        foods: list[UUID4 | str] | None = Query(None),
        households: list[UUID4 | str] | None = Query(None),
    ):
        cookbook_data: ReadCookBook | None = None
        if search_query.cookbook:
            if isinstance(search_query.cookbook, UUID):
                cb_match_attr = "id"
            else:
                try:
                    UUID(search_query.cookbook)
                    cb_match_attr = "id"
                except ValueError:
                    cb_match_attr = "slug"
            cookbook_data = self.group_cookbooks.get_one(search_query.cookbook, cb_match_attr)

            if cookbook_data is None:
                raise HTTPException(status_code=404, detail="cookbook not found")

        # We use "group_recipes" here so we can return all recipes regardless of household. The query filter can
        # include a household_id to filter by household.
        # We use "by_user" so we can sort favorites and other user-specific data correctly.
        pagination_response = self.group_recipes.by_user(self.user.id).page_all(
            pagination=q,
            cookbook=cookbook_data,
            categories=categories,
            tags=tags,
            tools=tools,
            foods=foods,
            households=households,
            require_all_categories=search_query.require_all_categories,
            require_all_tags=search_query.require_all_tags,
            require_all_tools=search_query.require_all_tools,
            require_all_foods=search_query.require_all_foods,
            search=search_query.search,
        )

        # merge default pagination with the request's query params
        query_params = q.model_dump() | {**request.query_params}
        pagination_response.set_pagination_guides(
            router.url_path_for("get_all"),
            {k: v for k, v in query_params.items() if v is not None},
        )

        json_compatible_response = orjson.dumps(pagination_response.model_dump(by_alias=True))

        # Response is returned directly, to avoid validation and improve performance
        return JSONBytes(content=json_compatible_response)

    @router.get("/suggestions", response_model=RecipeSuggestionResponse)
    def suggest_recipes(
        self,
        q: RecipeSuggestionQuery = Depends(make_dependable(RecipeSuggestionQuery)),
        foods: list[UUID4] | None = Query(None),
        tools: list[UUID4] | None = Query(None),
    ) -> RecipeSuggestionResponse:
        group_recipes_by_user = get_repositories(
            self.session, group_id=self.group_id, household_id=None
        ).recipes.by_user(self.user.id)

        recipes = group_recipes_by_user.find_suggested_recipes(q, foods, tools)
        response = RecipeSuggestionResponse(items=recipes)
        json_compatible_response = orjson.dumps(response.model_dump(by_alias=True))

        # Response is returned directly, to avoid validation and improve performance
        return JSONBytes(content=json_compatible_response)

    @router.get("/{slug}", response_model=Recipe)
    def get_one(self, slug: str = Path(..., description="A recipe's slug or id")):
        """Takes in a recipe's slug or id and returns all data for a recipe"""
        try:
            recipe = self.service.get_one(slug)
        except Exception as e:
            self.handle_exceptions(e)
            return None

        return recipe

    @router.post("/{slug}/parse-instruction-timers", response_model=ParseInstructionTimersOut)
    def parse_instruction_timers(self, slug: str, data: ParseInstructionTimersIn) -> ParseInstructionTimersOut:
        """
        Parse timer durations from instruction text provided by the client for a single recipe.
        This endpoint does not persist any data.
        """
        # Ensure the recipe exists and the user has access to it.
        self.service.get_one(slug)

        duration_parser = DurationParser()
        parsed_steps: list[ParseInstructionTimersStepOut] = []

        for step in data.steps:
            step_text = step.text.strip()
            if not step_text:
                continue

            durations = duration_parser.get_all_durations(step_text)
            if not durations:
                continue

            timers = [
                RecipeTimer(id=uuid4(), duration=int(duration), text=None, timers_active=[]) for duration in durations
            ]
            parsed_steps.append(ParseInstructionTimersStepOut(index=step.index, timers=timers))

        return ParseInstructionTimersOut(steps=parsed_steps)

    @router.post("/{slug}/parse-with-ai", response_model=ParseRecipeWithAIOut)
    async def parse_recipe_with_ai(self, slug: str, data: ParseRecipeWithAIIn) -> ParseRecipeWithAIOut:
        """
        Parse recipe editor data with OpenAI. This endpoint does not persist any data.
        """
        # Ensure the recipe exists and the user has access to it.
        self.service.get_one(slug)

        if not self.settings.OPENAI_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.respond(message="OpenAI is not enabled"),
            )

        openai_service = OpenAIService()
        prompt = self._get_parse_recipe_with_ai_prompt(openai_service)

        recipe_payload = {
            "orgURL": data.org_url,
            "ingredients": [
                {
                    "referenceId": str(ingredient.reference_id) if ingredient.reference_id else None,
                    "text": ingredient.display,
                }
                for ingredient in data.recipe_ingredient
            ],
            "instructions": [
                {
                    "id": str(step.id) if step.id else None,
                    "text": step.text,
                    "ingredientReferences": [
                        {"referenceId": str(ref.reference_id) if ref.reference_id else None}
                        for ref in step.ingredient_references
                    ],
                }
                for step in data.recipe_instructions
            ],
        }

        try:
            response = await openai_service.get_response(
                prompt,
                orjson.dumps(recipe_payload).decode("utf-8"),
                response_schema=OpenAIRecipe,
            )
        except Exception as ex:
            self.logger.exception(ex)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse.respond(message="Failed to parse recipe with AI"),
            ) from ex

        if not response:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=ErrorResponse.respond(message="OpenAI returned an empty response"),
            )

        ingredient_parser = OpenAIParser(self.group_id, self.session, self.translator)

        seen_ingredient_reference_ids: set[UUID] = set()
        ingredients: list[ParseRecipeWithAIIngredientItemOut] = []
        for i, ai_ingredient in enumerate(response.ingredients):
            if not ai_ingredient.text:
                continue

            fallback_reference_id = data.recipe_ingredient[i].reference_id if i < len(data.recipe_ingredient) else None
            reference_id = self._resolve_unique_uuid(
                preferred=self._parse_uuid(ai_ingredient.reference_id),
                fallback=fallback_reference_id,
                seen=seen_ingredient_reference_ids,
            )

            ingredients.append(
                self._build_parse_recipe_with_ai_ingredient_out(
                    ingredient_parser=ingredient_parser,
                    data=data,
                    index=i,
                    ai_ingredient=ai_ingredient,
                    reference_id=reference_id,
                )
            )

        seen_instruction_ids: set[UUID] = set()
        instructions: list[ParseRecipeWithAIStepItemOut] = []
        for i, ai_instruction in enumerate(response.instructions):
            if not ai_instruction.text:
                continue

            fallback_instruction_id = data.recipe_instructions[i].id if i < len(data.recipe_instructions) else None
            instruction_id = self._resolve_unique_uuid(
                preferred=self._parse_uuid(ai_instruction.id),
                fallback=fallback_instruction_id,
                seen=seen_instruction_ids,
            )

            instructions.append(
                ParseRecipeWithAIStepItemOut(
                    id=instruction_id,
                    title=ai_instruction.title,
                    text=ai_instruction.text,
                    ingredient_references=[
                        IngredientReferences(reference_id=self._parse_uuid(reference.reference_id))
                        for reference in ai_instruction.ingredient_references
                        if self._parse_uuid(reference.reference_id)
                    ],
                    timers=[
                        RecipeTimer(duration=timer.duration, text=timer.text, timers_active=[])
                        for timer in ai_instruction.timers
                        if 0 < timer.duration <= 176400
                    ],
                    preparation_instruction_id=self._parse_uuid(ai_instruction.preparation_instruction_id),
                    ingredients_with_quantity=[
                        ParseRecipeWithAIIngredientWithQuantityOut(
                            reference_id=self._parse_uuid(item.reference_id),
                            quantity=item.quantity,
                            quantity_in_ml=item.quantity_in_ml,
                            unit_name=item.unit_name,
                            comment=item.comment,
                        )
                        for item in (ai_instruction.ingredients_with_quantity or [])
                    ],
                )
            )

        return ParseRecipeWithAIOut(
            recipe_ingredient=ingredients,
            recipe_instructions=instructions,
            org_url=data.org_url,
            primary_unit_system=response.primary_unit_system,
        )

    @router.post("/{slug}/parse-instructions-with-ai", response_model=ParseRecipeInstructionsWithAIOut)
    async def parse_instructions_with_ai(
        self, slug: str, data: ParseRecipeInstructionsWithAIIn
    ) -> ParseRecipeInstructionsWithAIOut:
        """
        Parse recipe instructions with OpenAI to enrich timers and temperature text.
        This endpoint does not persist any data.
        """
        self.service.get_one(slug)

        if not self.settings.OPENAI_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.respond(message="OpenAI is not enabled"),
            )

        openai_service = OpenAIService()
        prompt = self._get_parse_instruction_timers_with_ai_prompt(openai_service)

        recipe_payload: dict[str, object] = {
            "primaryUnitSystem": data.primary_unit_system,
            "orgURL": data.org_url,
            "instructions": [
                {
                    "id": str(step.id) if step.id else None,
                    "text": step.text,
                    "timers": [],
                }
                for step in data.instructions
            ],
        }

        try:
            response = await openai_service.get_response(
                prompt,
                orjson.dumps(recipe_payload).decode("utf-8"),
                response_schema=OpenAIRecipeInstructionTimerResult,
            )
        except Exception as ex:
            self.logger.exception(ex)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse.respond(message="Failed to parse recipe instructions with AI"),
            ) from ex

        if not response:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=ErrorResponse.respond(message="OpenAI returned an empty response"),
            )

        seen_instruction_ids: set[UUID] = set()
        instructions: list[ParseRecipeInstructionsWithAIStepOut] = []
        for i, ai_instruction in enumerate(response.instructions):
            if not ai_instruction.text:
                continue

            fallback_instruction_id = data.instructions[i].id if i < len(data.instructions) else None
            instruction_id = self._resolve_unique_uuid(
                preferred=self._parse_uuid(ai_instruction.id),
                fallback=fallback_instruction_id,
                seen=seen_instruction_ids,
            )

            instructions.append(
                ParseRecipeInstructionsWithAIStepOut(
                    id=instruction_id,
                    text=ai_instruction.text,
                    timers=[
                        RecipeTimer(duration=timer.duration, text=timer.text, timers_active=[])
                        for timer in ai_instruction.timers
                        if 0 < timer.duration <= 176400
                    ],
                )
            )

        return ParseRecipeInstructionsWithAIOut(instructions=instructions)

    @router.post("", status_code=201, response_model=str)
    def create_one(self, data: CreateRecipe) -> str | None:
        """Takes in a JSON string and loads data into the database as a new entry"""
        try:
            new_recipe = self.service.create_one(data)
        except Exception as e:
            self.handle_exceptions(e)
            return None

        if new_recipe:
            self.publish_event(
                event_type=EventTypes.recipe_created,
                document_data=EventRecipeData(operation=EventOperation.create, recipe_slug=new_recipe.slug),
                group_id=new_recipe.group_id,
                household_id=new_recipe.household_id,
                message=self.t(
                    "notifications.generic-created-with-url",
                    name=new_recipe.name,
                    url=urls.recipe_url(self.group.slug, new_recipe.slug, self.settings.BASE_URL),
                ),
            )

        return new_recipe.slug

    @router.post("/{slug}/duplicate", status_code=201, response_model=Recipe)
    def duplicate_one(self, slug: str, req: RecipeDuplicate) -> Recipe:
        """Duplicates a recipe with a new custom name if given"""
        try:
            new_recipe = self.service.duplicate_one(slug, req)
        except Exception as e:
            self.handle_exceptions(e)

        if new_recipe:
            self.publish_event(
                event_type=EventTypes.recipe_created,
                document_data=EventRecipeData(operation=EventOperation.create, recipe_slug=new_recipe.slug),
                group_id=new_recipe.group_id,
                household_id=new_recipe.household_id,
                message=self.t(
                    "notifications.generic-duplicated",
                    name=new_recipe.name,
                ),
            )

        return new_recipe

    @router.put("/{slug}")
    def update_one(self, slug: str, data: Recipe):
        """Updates a recipe by existing slug and data."""
        try:
            recipe = self.service.update_one(slug, data)
        except Exception as e:
            self.handle_exceptions(e)

        if recipe:
            self.publish_event(
                event_type=EventTypes.recipe_updated,
                document_data=EventRecipeData(operation=EventOperation.update, recipe_slug=recipe.slug),
                group_id=recipe.group_id,
                household_id=recipe.household_id,
                message=self.t(
                    "notifications.generic-updated-with-url",
                    name=recipe.name,
                    url=urls.recipe_url(self.group.slug, recipe.slug, self.settings.BASE_URL),
                ),
            )

        return recipe

    @router.put("")
    def update_many(self, data: list[Recipe]):
        updated_by_group_and_household: defaultdict[UUID4, defaultdict[UUID4, list[Recipe]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for recipe in data:
            r = self.service.update_one(recipe.id, recipe)  # type: ignore
            updated_by_group_and_household[r.group_id][r.household_id].append(r)

        all_updated: list[Recipe] = []
        if updated_by_group_and_household:
            for group_id, household_dict in updated_by_group_and_household.items():
                for household_id, updated_recipes in household_dict.items():
                    all_updated.extend(updated_recipes)
                    self.publish_event(
                        event_type=EventTypes.recipe_updated,
                        document_data=EventRecipeBulkData(
                            operation=EventOperation.update, recipe_slugs=[r.slug for r in updated_recipes]
                        ),
                        group_id=group_id,
                        household_id=household_id,
                    )

        return all_updated

    @router.patch("/{slug}")
    def patch_one(self, slug: str, data: Recipe):
        """Updates a recipe by existing slug and data."""
        try:
            recipe = self.service.patch_one(slug, data)
        except Exception as e:
            self.handle_exceptions(e)

        if recipe:
            self.publish_event(
                event_type=EventTypes.recipe_updated,
                document_data=EventRecipeData(operation=EventOperation.update, recipe_slug=recipe.slug),
                group_id=recipe.group_id,
                household_id=recipe.household_id,
                message=self.t(
                    "notifications.generic-updated-with-url",
                    name=recipe.name,
                    url=urls.recipe_url(self.group.slug, recipe.slug, self.settings.BASE_URL),
                ),
            )

        return recipe

    @router.patch("")
    def patch_many(self, data: list[Recipe]):
        updated_by_group_and_household: defaultdict[UUID4, defaultdict[UUID4, list[Recipe]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for recipe in data:
            r = self.service.patch_one(recipe.id, recipe)  # type: ignore
            updated_by_group_and_household[r.group_id][r.household_id].append(r)

        all_updated: list[Recipe] = []
        if updated_by_group_and_household:
            for group_id, household_dict in updated_by_group_and_household.items():
                for household_id, updated_recipes in household_dict.items():
                    all_updated.extend(updated_recipes)
                    self.publish_event(
                        event_type=EventTypes.recipe_updated,
                        document_data=EventRecipeBulkData(
                            operation=EventOperation.update, recipe_slugs=[r.slug for r in updated_recipes]
                        ),
                        group_id=group_id,
                        household_id=household_id,
                    )

        return all_updated

    @router.patch("/{slug}/last-made")
    def update_last_made(self, slug: str, data: RecipeLastMade):
        """Update a recipe's last made timestamp"""

        try:
            recipe = self.service.update_last_made(slug, data.timestamp)
        except Exception as e:
            self.handle_exceptions(e)

        if recipe:
            self.publish_event(
                event_type=EventTypes.recipe_updated,
                document_data=EventRecipeData(operation=EventOperation.update, recipe_slug=recipe.slug),
                group_id=recipe.group_id,
                household_id=recipe.household_id,
                message=self.t(
                    "notifications.generic-updated-with-url",
                    name=recipe.name,
                    url=urls.recipe_url(self.group.slug, recipe.slug, self.settings.BASE_URL),
                ),
            )

        return recipe

    @router.delete("/{slug}")
    def delete_one(self, slug: str):
        """Deletes a recipe by slug"""
        try:
            recipe = self.service.delete_one(slug)
        except Exception as e:
            self.handle_exceptions(e)

        if recipe:
            self.publish_event(
                event_type=EventTypes.recipe_deleted,
                document_data=EventRecipeData(operation=EventOperation.delete, recipe_slug=recipe.slug),
                group_id=recipe.group_id,
                household_id=recipe.household_id,
                message=self.t("notifications.generic-deleted", name=recipe.name),
            )

        return recipe

    # ==================================================================================================================
    # Image and Assets

    @router.post("/{slug}/image", tags=["Recipe: Images and Assets"])
    async def scrape_image_url(self, slug: str, url: ScrapeRecipe):
        recipe = self.mixins.get_one(slug)
        data_service = RecipeDataService(recipe.id)

        try:
            await data_service.scrape_image(url.url)
        except NotAnImageError as e:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse.respond("Url is not an image"),
            ) from e
        except InvalidDomainError as e:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse.respond("Url is not from an allowed domain"),
            ) from e

        recipe.image = cache.cache_key.new_key()
        self.service.update_one(recipe.slug, recipe)

    @router.put("/{slug}/image", response_model=UpdateImageResponse, tags=["Recipe: Images and Assets"])
    def update_recipe_image(self, slug: str, image: bytes = File(...), extension: str = Form(...)):
        try:
            new_version = self.service.update_recipe_image(slug, image, extension)
            return UpdateImageResponse(image=new_version)
        except Exception as e:
            self.handle_exceptions(e)
            return None

    @router.delete("/{slug}/image", tags=["Recipe: Images and Assets"])
    def delete_recipe_image(self, slug: str):
        try:
            self.service.delete_recipe_image(slug)
            return SuccessResponse.respond(message=self.t("recipe.recipe-image-deleted"))
        except Exception as e:
            self.handle_exceptions(e)
            return None

    @router.post("/{slug}/assets", response_model=RecipeAsset, tags=["Recipe: Images and Assets"])
    def upload_recipe_asset(
        self,
        slug: str,
        name: str = Form(...),
        icon: str = Form(...),
        extension: str = Form(...),
        file: UploadFile = File(...),
    ):
        """Upload a file to store as a recipe asset"""
        if "." in extension:
            extension = extension.split(".")[-1]

        extension = extension.lower()
        if extension not in ASSET_ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported file extension")

        file_slug = slugify(name)
        if not extension or not file_slug:
            raise HTTPException(status_code=400, detail="Missing required fields")

        file_name = f"{file_slug}.{extension}"
        asset_in = RecipeAsset(name=name, icon=icon, file_name=file_name)

        recipe = self.service.get_one(slug)

        dest = recipe.asset_dir / file_name

        # Ensure path is relative to the recipe's asset directory
        if dest.absolute().parent != recipe.asset_dir:
            raise HTTPException(
                status_code=400,
                detail=f"File name {file_name} or extension {extension} not valid",
            )

        with dest.open("wb") as buffer:
            copyfileobj(file.file, buffer)

        if not dest.is_file():
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR)

        if recipe.assets is not None:
            recipe.assets.append(asset_in)

        self.service.update_one(slug, recipe)

        return asset_in
