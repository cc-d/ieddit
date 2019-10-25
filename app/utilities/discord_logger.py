"""
Sends messages to a discord server, mainly intended for logging.
"""
import os, sys
abspath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, abspath) 
os.chdir(abspath)

from discord_webhook import DiscordWebhook, DiscordEmbed
import config


webhook = DiscordWebhook(url=config.DISCORD_URL)

def send_discord_msg(title='error', description='An error occured'):
    """
    sends a message to discord
    """
    embed = DiscordEmbed(title=title, description=str(description), color=16711680)
    webhook.add_embed(embed)
    webhook.execute()
    return True

if __name__ == '__main__':
    send_discord_msg(title='test', description='test')
