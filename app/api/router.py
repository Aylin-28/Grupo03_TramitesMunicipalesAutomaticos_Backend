from fastapi import APIRouter

from app.modules.auth.routes import router as auth_router
from app.modules.ai.routes import router as ai_router
from app.modules.feedback.routes import router as feedback_router
from app.modules.admin.routes import router as admin_router

api_router = APIRouter()

api_router.include_router(auth_router,prefix="/auth",tags=["Auth"])
api_router.include_router(ai_router,prefix="/ai",tags=["Ai"])
api_router.include_router(feedback_router,prefix="/feedback",tags=["Feedback"])
api_router.include_router(admin_router,prefix="/admin",tags=["Admin"])