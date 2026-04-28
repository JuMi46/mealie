/* tslint:disable */

/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface MultiPurposeLabelCreate {
  name: string;
  color?: string;
  labelText?: string | null;
  position?: number | null;
  place?: string | null;
}
export interface MultiPurposeLabelOut {
  name: string;
  color?: string;
  groupId: string;
  id: string;
  labelText?: string | null;
  position?: number | null;
  sortOrder?: number | null;
  place?: string | null;
}
export interface MultiPurposeLabelSave {
  name: string;
  color?: string;
  labelText?: string | null;
  position?: number | null;
  place?: string | null;
  groupId: string;
}
export interface MultiPurposeLabelSummary {
  name: string;
  color?: string;
  groupId: string;
  id: string;
  labelText?: string | null;
  position?: number | null;
  sortOrder?: number | null;
  place?: string | null;
}
export interface MultiPurposeLabelUpdate {
  name: string;
  color?: string;
  labelText?: string | null;
  position?: number | null;
  place?: string | null;
  groupId: string;
  id: string;
}
