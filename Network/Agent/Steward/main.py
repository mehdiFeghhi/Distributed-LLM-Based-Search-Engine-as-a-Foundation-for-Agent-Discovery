from pyrogram import Client, filters
from model import Steward  # Assuming your Steward class is in model.py
import logging
# Replace the values with your own details
API_ID = ""  # Get this from my.telegram.org
API_HASH = ""  # Get this from my.telegram.org
BOT_TOKEN = ""  # Get this from @BotFather
TARGET_USER_ID = ""  # The user_id of the person




# Initialize the bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Initialize the Steward class
steward = Steward()

# Message handler to respond based on user input
@app.on_message(filters.private & filters.text)  # Respond to private text messages
async def handle_message(client, message):
    user_message = message.text  # Get the text of the user's message

    # Proceed only if the message is from the target user
    if message.from_user.id == TARGET_USER_ID:
        logging.info(f"Received message from {message.from_user.first_name}: {user_message}")

        # Send the message to Steward for processing
        try:
            ack_message = await message.reply("Your message has been received. Processing...")  # Quick acknowledgment
            response_message = steward.handler(user_message)  # Process the message
            
            # Delete the acknowledgment message
            await ack_message.delete()

            await app.send_message(TARGET_USER_ID, response_message)  # Send the response to the target user
            logging.info(f"Response sent to target user {message.from_user.first_name}: {response_message}")
        except Exception as e:
            logging.error(f"Error processing message from {message.from_user.first_name}: {str(e)}")
            await app.send_message(TARGET_USER_ID, "Unfortunately, there was an issue processing your request.")

            
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)  # Set logging level to INFO
    app.run()  # Start the bot
