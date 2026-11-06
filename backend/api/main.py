from fastapi import FastAPI
from .routers import auth,workspace,users,attendance,ai,system,records,files
api_app=FastAPI(title="Tech4Future-Global API",version="13.0",docs_url="/docs",redoc_url=None)
for r in [auth.router,workspace.router,users.router,attendance.router,ai.router,system.router,records.router,files.router]: api_app.include_router(r)
