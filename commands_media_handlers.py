# Media Info Feature - Add these to your existing commands.py

import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import get_file_details
from util.media_info_complete import media_extractor
import logging

logger = logging.getLogger(__name__)

@Client.on_callback_query(filters.regex(r"^mediainfo#"))
async def media_info_callback(client, query):
    """Handle media info button callback"""
    try:
        _, file_id = query.data.split("#")
        
        # Get file details from database
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer("❌ File not found!", show_alert=True)
        
        files = files_[0]
        file_name = files.file_name
        
        # Show processing message
        processing_msg = await query.message.reply_text(
            "🔄 <b>Extracting media information...</b>\n\n"
            f"📁 Analyzing: <code>{file_name}</code>\n"
            "This may take a few seconds...",
            quote=True
        )
        
        # Extract media info
        media_info = await media_extractor.extract_media_info(client, file_id, file_name)
        
        if media_info:
            # Format the information message
            info_message = media_extractor.format_media_info_message(media_info, file_name)
            
            # Add close button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close Info", callback_data="close_mediainfo")]
            ])
            
            # Edit the processing message with media info
            await processing_msg.edit_text(
                text=info_message,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML
            )
            
            # Auto-delete after 2 minutes to keep chat clean
            asyncio.create_task(auto_delete_media_info(processing_msg, 120))
            
        else:
            await processing_msg.edit_text(
                "❌ <b>Could not extract media information</b>\n\n"
                f"📁 File: <code>{file_name}</code>\n"
                "• File format might not be supported\n"
                "• File might be corrupted\n"
                "• Download may have failed\n\n"
                "<i>Check bot logs for detailed error information.</i>"
            )
            
            # Auto-delete after 30 seconds
            asyncio.create_task(auto_delete_media_info(processing_msg, 30))
        
        await query.answer()
        
    except Exception as e:
        logger.error(f"Error in media info callback: {e}")
        await query.answer("❌ Error extracting media information", show_alert=True)

@Client.on_callback_query(filters.regex(r"^close_mediainfo"))
async def close_media_info(client, query):
    """Handle close media info button"""
    try:
        await query.message.delete()
        await query.answer("Media info closed")
    except Exception as e:
        logger.error(f"Error closing media info: {e}")
        await query.answer()

async def auto_delete_media_info(message, delay_seconds):
    """Auto delete media info message after specified delay"""
    try:
        await asyncio.sleep(delay_seconds)
        await message.delete()
    except Exception as e:
        logger.error(f"Error auto-deleting media info: {e}")

# Note: Also add this button to your file sending sections:
# [InlineKeyboardButton('📋 Media Info', callback_data=f'mediainfo#{file_id}')]