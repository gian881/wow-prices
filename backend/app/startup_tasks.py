import httpx
from sqlmodel import Session, select

from app.dependencies import engine
from app.models import Item, ItemCache
from app.utils import (
    BUCKET_NAME,
    download_image_and_upload_to_supabase,
    get_item_blizzard_image_url,
    log,
    supabase_client,
)


async def verify_images_on_startup():
    """
    Checks if all images in the 'items' table exist in Supabase Storage.
    If an image is missing, it re-downloads and uploads it.
    """
    log("Starting image verification task...")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            with Session(engine) as session:
                items = session.exec(select(Item.id, Item.image_path)).all()
                if not items:
                    return

                storage_files_list = supabase_client.storage.from_(
                    BUCKET_NAME
                ).list()

                existing_storage_files = {
                    file["name"] for file in storage_files_list
                }

                missing_count = 0
                for item_id, image_path in items:
                    if not image_path:
                        continue

                    file_name = image_path.split("/")[-1][
                        :-1
                    ]  # Removing the "?"

                    if file_name not in existing_storage_files:
                        missing_count += 1
                        log(
                            f"❗️ Image '{file_name}' for item ID {item_id} is missing. Attempting to re-upload..."
                        )

                        # Verifies if we have a cached Blizzard URL for this item
                        cache_entry = session.exec(
                            select(ItemCache.blizzard_image_url).where(
                                ItemCache.item_id == item_id
                            )
                        ).first()

                        if not cache_entry:
                            # If it doesn't exist, we get it from the Blizzard API
                            blizzard_url = await get_item_blizzard_image_url(
                                client, item_id
                            )
                            if not blizzard_url:
                                log(
                                    f"   - ❌ Could not find Blizzard URL in cache or API for item ID {item_id}."
                                )
                                continue
                        else:
                            blizzard_url = cache_entry

                        try:
                            await download_image_and_upload_to_supabase(
                                client, blizzard_url, file_name
                            )
                        except Exception as e:
                            log(
                                f"   - ❌ Failed to re-upload '{file_name}': {e}"
                            )
        except Exception as e:
            log(f"An error occurred during image verification: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(verify_images_on_startup())
