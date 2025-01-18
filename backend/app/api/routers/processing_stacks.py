from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database.models import ProcessingStack, ProcessingStep, ProcessingStackStep
from app.services.database import get_db_session
from app.services.processing_stacks import (
    create_empty_processing_stack,
    add_processing_stack_step,
    change_processing_stack_step_order,
    delete_processing_stack_step,
    create_processing_step,
    generate_stack_identifier,
    delete_processing_stack
)

import logging

logger = logging.getLogger("uvicorn")

processing_stacks_router = r = APIRouter()

class ProcessingStepCreate(BaseModel):
    identifier: str
    display_name: str
    description: Optional[str] = None
    type: str
    parameters_schema: dict

class ProcessingStackStepUpdate(BaseModel):
    step_identifier: str
    order: int
    parameters: Optional[dict] = None

class ProcessingStackUpdate(BaseModel):
    steps: List[ProcessingStackStepUpdate]
    supported_extensions: Optional[List[str]] = None

class ProcessingStackCreate(BaseModel):
    display_name: str
    description: Optional[str] = None
    supported_extensions: Optional[List[str]] = None
    steps: List[ProcessingStackStepUpdate]

@r.get("/steps")
async def get_processing_steps_route(session: Session = Depends(get_db_session)):
    try:
        steps = session.query(ProcessingStep).all()
        return [
            {
                "identifier": step.identifier,
                "display_name": step.display_name,
                "description": step.description,
                "type": step.type,
                "parameters_schema": step.parameters_schema
            }
            for step in steps
        ]
    except Exception as e:
        logger.error(f"Error getting processing steps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@r.get("/stacks")
async def get_processing_stacks_route(session: Session = Depends(get_db_session)):
    try:
        stacks = session.query(ProcessingStack).all()
        return [
            {
                "identifier": stack.identifier,
                "display_name": stack.display_name,
                "description": stack.description,
                "is_enabled": stack.is_enabled,
                "steps": [
                    {
                        "id": step.id,
                        "order": step.order,
                        "parameters": step.parameters,
                        "step_identifier": step.step_identifier,
                        "step": {
                            "identifier": step.step.identifier,
                            "display_name": step.step.display_name,
                            "description": step.step.description,
                            "type": step.step.type,
                            "parameters_schema": step.step.parameters_schema
                        }
                    }
                    for step in sorted(stack.steps, key=lambda x: x.order)
                ]
            }
            for stack in stacks
        ]
    except Exception as e:
        logger.error(f"Error getting processing stacks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@r.post("/stacks")
async def create_processing_stack_route(
    stack: ProcessingStackCreate,
    session: Session = Depends(get_db_session)
):
    try:
        # Check for invalid characters in display name
        invalid_chars = '<>:"|?*\\'
        if any(char in stack.display_name for char in invalid_chars):
            raise ValueError(
                f"Processing stack display name contains invalid characters. The following characters are not allowed: {invalid_chars}"
            )

        # Generate identifier
        stack_identifier = generate_stack_identifier(stack.display_name)

        create_empty_processing_stack(
            session=session,
            stack_identifier=stack_identifier,
            display_name=stack.display_name,
            description=stack.description,
            supported_extensions=stack.supported_extensions
        )
        
        # Add steps
        for step in stack.steps:
            add_processing_stack_step(
                session=session,
                stack_identifier=stack_identifier,
                step_identifier=step.step_identifier,
                order=step.order,
                parameters=step.parameters or {}
            )

        return {
            "identifier": stack_identifier,
            "display_name": stack.display_name,
            "description": stack.description,
            "is_enabled": True,
            "steps": stack.steps
        }

    except Exception as e:
        logger.error(f"Error creating processing stack: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@r.put("/stacks/{stack_identifier}")
async def update_processing_stack_route(
    stack_identifier: str,
    stack_update: ProcessingStackUpdate,
    session: Session = Depends(get_db_session)
):
    try:
        db_stack = session.query(ProcessingStack).filter_by(identifier=stack_identifier).first()
        if not db_stack:
            raise HTTPException(status_code=404, detail="Stack not found")
        
        # Update supported extensions if provided
        if stack_update.supported_extensions is not None:
            db_stack.supported_extensions = stack_update.supported_extensions
        
        # Delete existing steps
        session.query(ProcessingStackStep).filter_by(stack_identifier=stack_identifier).delete()
        
        # Add new steps
        for step in stack_update.steps:
            add_processing_stack_step(
                session=session,
                stack_identifier=stack_identifier,
                step_identifier=step.step_identifier,
                order=step.order,
                parameters=step.parameters or {}
            )
        
        session.commit()
        
        # Return updated stack
        updated_stack = session.query(ProcessingStack).filter_by(identifier=stack_identifier).first()
        return {
            "identifier": updated_stack.identifier,
            "display_name": updated_stack.display_name,
            "description": updated_stack.description,
            "is_enabled": updated_stack.is_enabled,
            "steps": [
                {
                    "id": step.id,
                    "order": step.order,
                    "parameters": step.parameters,
                    "step_identifier": step.step_identifier,
                    "step": {
                        "identifier": step.step.identifier,
                        "display_name": step.step.display_name,
                        "description": step.step.description,
                        "type": step.step.type,
                        "parameters_schema": step.step.parameters_schema
                    }
                }
                for step in sorted(updated_stack.steps, key=lambda x: x.order)
            ]
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating processing stack: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@r.delete("/stacks/{stack_identifier}")
async def delete_processing_stack_route(
    stack_identifier: str,
    session: Session = Depends(get_db_session)
):
    try:
        delete_processing_stack(session, stack_identifier)
        return {"message": "Stack deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting processing stack: {e}")
        raise HTTPException(status_code=500, detail=str(e))
