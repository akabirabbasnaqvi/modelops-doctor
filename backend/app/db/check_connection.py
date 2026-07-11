import asyncio

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine


async def check_database_connection() -> None:
    """Connect to PostgreSQL and display basic server information."""

    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT current_database(), current_user, version()")
            )

            database_name, database_user, database_version = result.one()

            print("Database connection successful.")
            print(f"Database: {database_name}")
            print(f"User: {database_user}")
            print(f"Version: {database_version}")

    except SQLAlchemyError as error:
        print("Database connection failed.")
        print(f"Error: {error}")
        raise

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_database_connection())
