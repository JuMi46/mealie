import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from sqlalchemy import orm

from mealie.db.models.recipe.instruction import RecipeInstruction
from mealie.db.models.recipe.timer import RecipeTimerModel
from mealie.pkgs.stats import fs_stats
from mealie.routes._base import BaseAdminController, controller
from mealie.schema.admin import MaintenanceSummary
from mealie.schema.admin.maintenance import MaintenanceStorageDetails
from mealie.schema.response import ErrorResponse, SuccessResponse
from mealie.services.parser_services.parser_utils.duration_parser import DurationParser

router = APIRouter(prefix="/maintenance")


def clean_images(root_dir: Path, dry_run: bool) -> int:
    cleaned_images = 0

    for recipe_dir in root_dir.iterdir():
        image_dir = recipe_dir.joinpath("images")

        if not image_dir.exists():
            continue

        for image in image_dir.iterdir():
            if image.is_dir():
                continue

            if image.suffix != ".webp":
                if not dry_run:
                    image.unlink()

                cleaned_images += 1

    return cleaned_images


def clean_recipe_folders(root_dir: Path, dry_run: bool) -> int:
    cleaned_dirs = 0

    for recipe_dir in root_dir.iterdir():
        if recipe_dir.is_dir():
            # Attempt to convert the folder name to a UUID
            try:
                uuid.UUID(recipe_dir.name)
                continue
            except ValueError:
                if not dry_run:
                    shutil.rmtree(recipe_dir)
                cleaned_dirs += 1

    return cleaned_dirs


def tail_log(log_file: Path, n: int) -> list[str]:
    try:
        with open(log_file) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return ["no log file found"]

    return lines[-n:]


@controller(router)
class AdminMaintenanceController(BaseAdminController):
    @router.get("", response_model=MaintenanceSummary)
    def get_maintenance_summary(self):
        """
        Get the maintenance summary
        """

        return MaintenanceSummary(
            data_dir_size=fs_stats.pretty_size(fs_stats.get_dir_size(self.folders.DATA_DIR)),
            cleanable_images=clean_images(self.folders.RECIPE_DATA_DIR, dry_run=True),
            cleanable_dirs=clean_recipe_folders(self.folders.RECIPE_DATA_DIR, dry_run=True),
        )

    @router.get("/storage", response_model=MaintenanceStorageDetails)
    def get_storage_details(self):
        return MaintenanceStorageDetails(
            temp_dir_size=fs_stats.pretty_size(fs_stats.get_dir_size(self.folders.TEMP_DIR)),
            backups_dir_size=fs_stats.pretty_size(fs_stats.get_dir_size(self.folders.BACKUP_DIR)),
            groups_dir_size=fs_stats.pretty_size(fs_stats.get_dir_size(self.folders.GROUPS_DIR)),
            recipes_dir_size=fs_stats.pretty_size(fs_stats.get_dir_size(self.folders.RECIPE_DATA_DIR)),
            user_dir_size=fs_stats.pretty_size(fs_stats.get_dir_size(self.folders.USER_DIR)),
        )

    @router.post("/clean/images", response_model=SuccessResponse)
    def clean_images(self):
        """
        Purges all the images from the filesystem that aren't .webp
        """
        try:
            cleaned_images = clean_images(self.folders.RECIPE_DATA_DIR, dry_run=False)
            return SuccessResponse.respond(f"{cleaned_images} Images cleaned")
        except Exception as e:
            raise HTTPException(status_code=500, detail=ErrorResponse.respond("Failed to clean images")) from e

    @router.post("/clean/temp", response_model=SuccessResponse)
    def clean_temp(self):
        try:
            if self.folders.TEMP_DIR.exists():
                shutil.rmtree(self.folders.TEMP_DIR)

            self.folders.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=ErrorResponse.respond("Failed to clean temp")) from e

        return SuccessResponse.respond("'.temp' directory cleaned")

    @router.post("/clean/recipe-folders", response_model=SuccessResponse)
    def clean_recipe_folders(self):
        """
        Deletes all the recipe folders that don't have names that are valid UUIDs
        """
        try:
            cleaned_dirs = clean_recipe_folders(self.folders.RECIPE_DATA_DIR, dry_run=False)
            return SuccessResponse.respond(f"{cleaned_dirs} Recipe folders removed")
        except Exception as e:
            raise HTTPException(status_code=500, detail=ErrorResponse.respond("Failed to clean directories")) from e

    @router.post("/parse/instruction-timers", response_model=SuccessResponse)
    def parse_instruction_timers(self):
        """
        Parse and add instruction timers for instructions that do not already have timers.
        Safe to run multiple times without creating duplicates per instruction.
        """
        try:
            duration_parser = DurationParser()
            created_timers = 0
            parsed_instructions = 0
            skipped_instructions = 0

            instructions = (
                self.session.query(RecipeInstruction)
                .options(orm.selectinload(RecipeInstruction.timers))
                .filter(RecipeInstruction.text.isnot(None), RecipeInstruction.text != "")
                .all()
            )

            timers_to_create: list[RecipeTimerModel] = []
            for instruction in instructions:
                if instruction.timers:
                    skipped_instructions += 1
                    continue

                timers = duration_parser.get_all_durations(instruction.text or "")
                if not timers:
                    continue

                parsed_instructions += 1
                for timer in timers:
                    timers_to_create.append(
                        RecipeTimerModel(
                            id=uuid.uuid4(),
                            duration=int(timer),
                            text=None,
                            recipe_instruction_id=instruction.id,
                            session=self.session,
                        )
                    )
                    created_timers += 1

            if timers_to_create:
                self.session.add_all(timers_to_create)
                self.session.commit()

            return SuccessResponse.respond(
                f"Added {created_timers} timers across {parsed_instructions} instructions; "
                f"skipped {skipped_instructions} instructions that already had timers"
            )
        except Exception as e:
            self.session.rollback()
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse.respond("Failed to parse instruction timers"),
            ) from e
