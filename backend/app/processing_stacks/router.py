from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.models import ProcessingStack, ProcessingStep, ProcessingStackStep
from app.database.service import get_db_session
from app.api.utils import get_user_id
from app.processing_stacks.schemas import (
    ProcessingStackCreate,
    ProcessingStackUpdate,
    ProcessingStepResponse,
    ProcessingStackResponse,
    ProcessingStackStepResponse
)
from app.processing_stacks.service import (
    create_processing_stack,
    update_processing_stack,
    delete_processing_stack
)

import logging

logger = logging.getLogger("uvicorn")

processing_stacks_router = r = APIRouter()

@r.get(
    "/steps",
    response_model=List[ProcessingStepResponse]
)
async def get_processing_steps_route(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        steps = session.query(ProcessingStep).all()
        return [
            ProcessingStepResponse(
                identifier=step.identifier,
                display_name=step.display_name,
                description=step.description,
                type=step.type,
                parameters_schema=step.parameters_schema
            )
            for step in steps
        ]
    except Exception as e:
        logger.error(f"Error getting processing steps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@r.get(
    "/stacks",
    response_model=List[ProcessingStackResponse]
)
async def get_processing_stacks_route(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        stacks = session.query(ProcessingStack).all()
        return [
            ProcessingStackResponse(
                identifier=stack.identifier,
                display_name=stack.display_name,
                description=stack.description,
                is_enabled=stack.is_enabled,
                steps=[
                    ProcessingStackStepResponse(
                        id=step.id,
                        step_identifier=step.step_identifier,
                        order=step.order,
                        parameters=step.parameters,
                        step=ProcessingStepResponse(
                            identifier=step.step.identifier,
                            display_name=step.step.display_name,
                            description=step.step.description,
                            type=step.step.type,
                            parameters_schema=step.step.parameters_schema
                        )
                    )
                    for step in sorted(stack.steps, key=lambda x: x.order)
                ]
            )
            for stack in stacks
        ]
    except Exception as e:
        logger.error(f"Error getting processing stacks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@r.post(
    "/stacks",
    response_model=ProcessingStackResponse
)
async def create_processing_stack_route(
    stack: ProcessingStackCreate,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        logger.info(f"Creating processing stack {stack.display_name} for user {user_id}")
        response = create_processing_stack(session=session, stack=stack)
        return response

    except Exception as e:
        logger.error(f"Error creating processing stack: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@r.put(
    "/stacks/{stack_identifier}",
    response_model=ProcessingStackResponse
)
async def update_processing_stack_route(
    stack_identifier: str,
    stack_update: ProcessingStackUpdate,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        return update_processing_stack(session=session, stack_identifier=stack_identifier, stack_update=stack_update)
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating processing stack: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@r.delete("/stacks/{stack_identifier}")
async def delete_processing_stack_route(
    stack_identifier: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        delete_processing_stack(session=session, stack_identifier=stack_identifier)
        return {"message": "Stack deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting processing stack: {e}")
        raise HTTPException(status_code=500, detail=str(e))
