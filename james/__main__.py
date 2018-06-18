import discord
from discord.ext import commands
import asyncio
import json
import os
import difflib
import sys
import pickle
import math

TOKEN = 'NDM3MzIxOTQ3NDgzODY1MDk4.Db0YAg.PLZIhuXcnzH5XyA2xsXuU2oSObY'
James = commands.Bot(command_prefix='!', owner_id=195097871626928128, case_insensitive=True)
James.remove_command('help')

gyms = {}

def load_data():
    global guild_dict
    try:
        with open(os.path.join('data', 'guild_dict'), 'rb') as fd:
            guild_dict = pickle.load(fd)
    except OSError:
        with open(os.path.join('data', 'guild_dict'), 'wb') as fd:
            guild_dict = {}
            pickle.dump(guild_dict, fd, (- 1))
            
    global gyms
    with open(os.path.join('data', 'gyms.json'), 'r') as fd:
        gyms_data = json.load(fd)["Document"]["Folder"]
    for gym_folder in gyms_data:
        for gym in gym_folder["Placemark"]:
            gym_name = str(gym["name"]) if ("__cdata" not in gym["name"]) else str(gym["name"]["__cdata"])
            gym_coord = gym["Point"]["coordinates"].strip().split(',')[:2]
            gym_coord.reverse()
            gym_ex_confirmed = True if gym_folder["name"] == "Confirmed EX Gyms" else False
            
            gyms[gym_name.lower()] = {"Name": gym_name, "Coordinates": gym_coord, "Ex Confirmed": gym_ex_confirmed}
load_data()

async def save():
    with open(os.path.join('data', 'guild_dict_tmp'), 'wb') as fd:
        pickle.dump(guild_dict, fd, (- 1))
    os.remove(os.path.join('data', 'guild_dict'))
    os.rename(os.path.join('data', 'guild_dict_tmp'), os.path.join('data', 'guild_dict'))
  
"""
Events
"""

@James.event
async def on_ready():
    async def auto_save(loop=True):
        while (not James.is_closed()):
            try:
                await save()
            except Exception as err:
                pass
            await asyncio.sleep(600)
            continue
    
    try:
        event_loop.create_task(auto_save())
    except KeyboardInterrupt as e:
        pass
event_loop = asyncio.get_event_loop()

@James.event
async def on_guild_join(guild):
    guild_dict[guild.id] = {
        'region': None
    }

@James.event
async def on_guild_remove(guild):
    try:
        if guild.id in guild_dict:
            try:
                del guild_dict[guild.id]
            except KeyError:
                pass
    except KeyError:
        pass
        
@James.event
async def on_guild_channel_create(channel):
    if channel.guild != None:
        if channel.category.name.lower() == "raids":
            await asyncio.sleep(7)
            first_message = (await channel.history(reverse=True).flatten())[0]
            details_start_index = first_message.content.index("Details: ") + len("Details: ")
            details_end_index = first_message.content.index(".", details_start_index)
            raid_location_details = first_message.content[details_start_index:details_end_index]
            
            gym = await find_gym(raid_location_details, first_message.mentions[0], channel)
            if gym:
                maps_link = 'https://www.google.com/maps/search/?api=1&query={}'.format('+'.join(gym['Coordinates']))
                await channel.send(f'{maps_link}')
                if gym["Ex Confirmed"]:
                    role = discord.utils.get(channel.guild.roles, name="mewtwo")
                    await channel.send('{}Confirmed EX Gym in {}'.format((role.mention + " - ") if role else "", raid_location_details))

"""
Helper functions
"""  

async def find_gym(entered_gym, author, channel):
    entered_gym = entered_gym.lower()
    gym = gyms.get(entered_gym, None)
    if not gym:
        gym_autocorrect = autocorrect(entered_gym, gyms.keys(), author, channel)
        if gym_autocorrect:
            if await ask('The Gym name is {} ?'.format(gym_autocorrect.title()), author, channel):
                gym = gyms[gym_autocorrect]
    if not gym:
        pass#await channel.send("Use **!gym [gym_name]** to send the gym location.")
    return gym

def autocorrect(word, word_list, user, channel):
    close_matches = difflib.get_close_matches(word, word_list, n=1, cutoff=0.6)
    if ( len(close_matches) <= 0 ):
        return None
    return close_matches[0]

async def ask(message, user, channel):
    react_list = ['👍', '👎']
    rusure = await channel.send(message)
    def check(reaction, user_react):
        return reaction.message.id == rusure.id and user.id == user_react.id and (reaction.emoji in react_list)
    for r in react_list:
        await asyncio.sleep(0.25)
        await rusure.add_reaction(r)
    try:
        reaction, user = await James.wait_for('reaction_add', check=check, timeout=60)
        await rusure.delete()
        return reaction.emoji == '👍'
    except asyncio.TimeoutError:
        await rusure.delete()
        return False

def distanceBetweenCord(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    Source: https://gis.stackexchange.com/a/56589/15183
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    km = 6367 * c
    return km

"""
Commands
"""

@James.command()
async def gym(ctx):
    message = ctx.message
    channel = message.channel
    author = message.author
    guild = channel.guild
    
    args = message.clean_content.split()[1:]
    if len(args) == 0:
        await channel.send('Give me the gym name!')
        return
    entered_gym = ' '.join(args)
    gym = await find_gym(entered_gym, author, channel)
    if gym:
        maps_link = 'https://www.google.com/maps/search/?api=1&query={}'.format('+'.join(gym['Coordinates']))
        await channel.send(f'{maps_link}')
        if gym["Ex Confirmed"]:
            role = discord.utils.get(channel.guild.roles, name="mewtwo")
            await channel.send('{}Confirmed EX Gym in {}'.format((role.mention + " - ") if role else "", entered_gym))

@James.command(hidden=True)
async def dgym(ctx):
    message = ctx.message
    channel = message.channel
    author = message.author
    guild = channel.guild
    
    args = message.clean_content.split()[1:]
    if len(args) == 0:
        await channel.send('Give me the gym name!')
        return
    entered_gym = ' '.join(args)
    gym = await find_gym(entered_gym, author, channel)
    if gym:
        maps_link = 'https://www.google.com/maps/search/?api=1&query={}'.format('+'.join(gym['Coordinates']))
        await channel.send(f'{gym}')
            
@James.command(hidden=True)
async def region(ctx):
    message = ctx.message
    channel = message.channel
    guild = channel.guild
    
    args = message.clean_content.split()[1:]
    if len(args) == 0:
        await channel.send('Give me a region!')
        return
    region = ' '.join(args)
    guild_dict[guild.id]['region'] = region
    await message.add_reaction('☑')
    
"""
Admin Commands
"""    

@commands.is_owner()
@James.command(hidden=True)
async def reload(ctx):
    load_data()
    await ctx.message.add_reaction('☑')

@commands.is_owner()
@James.command(hidden=True)
async def restart(ctx):
    """Restart after saving.

    Usage: !restart.
    Calls the save function and restarts James."""
    await save()
    
    await ctx.channel.send('Restarting...')
    James._shutdown_mode = 26
    await James.logout()

@commands.is_owner()
@James.command(hidden=True)
async def exit(ctx):
    """Exit after saving.

    Usage: !exit.
    Calls the save function and quits the script."""
    await save()
    
    await ctx.channel.send('Shutting down...')
    James._shutdown_mode = 0
    await James.logout()
    
    
try:
    event_loop.run_until_complete(James.start(TOKEN))
except discord.LoginFailure:
    # Invalid token
    event_loop.run_until_complete(James.logout())
    James._shutdown_mode = 0
except KeyboardInterrupt:
    # Keyboard interrupt detected. Quitting...
    event_loop.run_until_complete(James.logout())
    James._shutdown_mode = 0
except Exception as e:
    # logger.critical('Fatal exception', exc_info=e)
    event_loop.run_until_complete(James.logout())
finally:
    pass
sys.exit(James._shutdown_mode) 