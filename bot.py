# bot.py
import os
import time
import subprocess
import asyncio
import json
import requests
import random
from PIL import Image, ImageFont, ImageDraw
import numpy as np
from dotenv import load_dotenv
from datetime import datetime
from discord import utils, File, Embed
from discord.ext import commands, tasks
from sandy_brain import Brain
from sandy_maps import MapGenerator

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')
brain = Brain()

@tasks.loop(seconds=1)
async def main_loop():
    if brain.alive_since is None:
        brain.alive_since = datetime.now()

@bot.command(name='spells', help="list 5e spells by class !spells wizard", pass_context=True)
async def spells(ctx, *args):
    school = args[0]
    level = args[1]
    spell_data = json.load(open("spells.json"))
    message = ""
    for spell in spell_data:
        if school.lower() in spell["tags"] and level.lower() == spell["level"]:
            message = message + spell["name"] + " - " + spell["type"] + "\n"
    await ctx.send(message)

@bot.command(name='vote', help="call a timed vote !vote \"<topic>\" <minutes>", pass_context=True)
async def quickvote(ctx, *args):
    user_id = str(ctx.message.author.id)
    if brain.check_role(user_id,"trader") is False:
        await ctx.send("You don't have permission to do that.")
        return
    topic = args[0]
    minutes = 1
    if len(args) > 1:
        try:
            minutes = int(args[1])
        except:
            do_nothing = True
    count_down = str(minutes) + " MINUTE"
    if minutes > 1:
        count_down = count_down + "S"
    msg = await ctx.send('CALL TO VOTE:\n'+topic+'\n\nVoting will close in '+count_down+'.')
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    await asyncio.sleep(60*minutes)
    cache_msg = utils.get(bot.cached_messages, id=msg.id)
    reply = 'VOTING CLOSED:\n'+topic+'\n\nRESULTS:\n'
    for reaction in cache_msg.reactions:
        reply = reply + "\t"+reaction.emoji+" - "+str(reaction.count-1)+"\n"
    if cache_msg.reactions[0].count > cache_msg.reactions[1].count:
        reply = reply + "The Vote Has PASSED"
    elif cache_msg.reactions[0].count == cache_msg.reactions[1].count:
        reply = reply + "The Vote Is TIED"
    else:
        reply = reply + "The Vote Has FAILED"
    await ctx.send(reply)

@bot.command(name='spell', help="look up a 5e spell", pass_context=True)
async def spell(ctx, arg):
    spell_data = json.load(open("spells.json"))
    spell = None
    for s in spell_data:
        if arg.lower() in s["name"].lower():
            spell = s
            break
    if spell is None:
        await ctx.send("That spell was not found.")
        return
    print(json.dumps(spell))
    embed=Embed(title=spell["name"], description="level: "+spell["level"] + " " + ", ".join(spell["classes"]), color=0x109319)
    # Add author, thumbnail, fields, and footer to the embed
    embed.set_author(name=spell["school"])

    #embed.set_thumbnail(url="https://i.imgur.com/axLm3p6.jpeg")
    embed.add_field(name="Range", value=spell["range"], inline=True) 
    embed.add_field(name="Duration", value=spell["duration"], inline=True) 
    # embed.add_field(name="Field 2 Title", value="It is inline with Field 3", inline=True)
    # embed.add_field(name="Field 3 Title", value="It is inline with Field 2", inline=True)

    embed.set_footer(text=spell["description"])

    #### Useful ctx variables ####
    ## User's display name in the server
    #ctx.author.display_name

    ## User's avatar URL
    #ctx.author.avatar_url
    await ctx.send(embed=embed)

@bot.command(name='rollstats', help="roll 5e stats (4d6 drop lowest)", pass_context=True)
async def rollstats(ctx):
    message = ""
    stat_rolls = []
    for i in range(6):
        rolls = []
        for x in range(4):
            roll = random.randint(1,6)
            rolls.append(roll)
            message = message + str(roll) + " "
        min_roll = min(rolls)
        total_roll = sum(rolls)
        final_roll = total_roll - min_roll
        message = message + "-drop: " + str(min_roll) + " -final: " + str(final_roll) +"\n"
    await ctx.send(message)

@bot.command(name='monster', help="look up 5e monster", pass_context=True)
async def monster(ctx, arg):
    url = "https://www.dnd5eapi.co/api/monsters"
    res = requests.get(url)
    data = res.json()
    l = data["results"]
    names = []
    for mon in l:
        if (len(arg) < 2 and mon["index"].startswith(arg.lower())) or (len(arg) > 1 and arg.lower() in mon["index"]):
            names.append(mon["index"])
    if len(names) == 0:
        await ctx.send("Not found.")
        return
    if len(names) > 1:
        await ctx.send("\n".join(names))
        return
    url = "https://www.dnd5eapi.co/api/monsters/"+names[0]
    res = requests.get(url)
    data = res.json()
    if "error" in data.keys():
        await ctx.send(data["error"])
        return
    embed=Embed(title=data["name"], description=data["size"], color=0x109319)
    embed.set_author(name=data["type"])
    embed.add_field(name="AC", value=data["armor_class"], inline=True) 
    embed.add_field(name="HP", value=data["hit_points"], inline=True) 
    embed.add_field(name="CR", value=data["challenge_rating"], inline=True) 
    if "speed" in data.keys():
        for subkey in data["speed"].keys():
            embed.add_field(name=subkey, value=data["speed"][subkey], inline=False) 
    embed.add_field(name="STR", value=data["strength"], inline=True) 
    embed.add_field(name="DEX", value=data["dexterity"], inline=True) 
    embed.add_field(name="CON", value=data["constitution"], inline=True) 
    embed.add_field(name="INT", value=data["intelligence"], inline=True) 
    embed.add_field(name="WIS", value=data["wisdom"], inline=True) 
    embed.add_field(name="CHA", value=data["charisma"], inline=True) 
    if "proficiencies" in data.keys():
        for proficiency in data["proficiencies"]:
            embed.add_field(name=proficiency["proficiency"]["name"], value=proficiency["value"], inline=True) 
    if "actions" in data.keys():
        for action in data["actions"]:
            embed.add_field(name=action["name"], value=action["desc"], inline=False) 
    if "damage_resistances" in data.keys() and len(data["damage_resistances"]) > 0:
        embed.add_field(name="Resistances", value="\n".join(data["damage_resistances"]), inline=False) 
    if "damage_vulnerabilities" in data.keys() and len(data["damage_vulnerabilities"]) > 0:
        embed.add_field(name="Vulnerabilities", value="\n".join(data["damage_vulnerabilities"]), inline=False) 
    if "damage_immunities" in data.keys() and len(data["damage_immunities"]) > 0:
        embed.add_field(name="Immunities", value="\n".join(data["damage_immunities"]), inline=False) 
    if "condition_immunities" in data.keys() and len(data["condition_immunities"]) > 0:
        embed.add_field(name="Cond. Immunities", value="\n".join(data["condition_immunities"]), inline=False) 
    #embed.set_footer(text=data["description"])
    await ctx.send(embed=embed)

@bot.command(name='equip', help="look up 5e equipment", pass_context=True)
async def equip(ctx, arg):
    url = "https://www.dnd5eapi.co/api/equipment"
    res = requests.get(url)
    data = res.json()
    l = data["results"]
    names = []
    for mon in l:
        if (len(arg) < 2 and mon["index"].startswith(arg.lower())) or (len(arg) > 1 and arg.lower() in mon["index"]):
            names.append(mon["index"])
    if len(names) == 0:
        await ctx.send("Not found.")
        return
    if len(names) > 1:
        await ctx.send("\n".join(names))
        return
    url = "https://www.dnd5eapi.co/api/equipment/"+names[0]
    res = requests.get(url)
    data = res.json()
    if "error" in data.keys():
        await ctx.send(data["error"])
        return
    embed=Embed(title=data["name"], color=0x109319)
    embed.set_author(name=data["equipment_category"]["name"])
    embed.add_field(name="Weight", value=data["weight"], inline=False) 
    if "cost" in data.keys():
        embed.add_field(name=data["cost"]["unit"], value=data["cost"]["quantity"], inline=True) 
    #embed.set_footer(text=data["description"])
    await ctx.send(embed=embed)

@bot.command(name='magicitem', help="look up 5e magic item", pass_context=True)
async def magicitem(ctx, arg):
    url = "https://www.dnd5eapi.co/api/magic-items"
    res = requests.get(url)
    data = res.json()
    l = data["results"]
    names = []
    for mon in l:
        if (len(arg) < 2 and mon["index"].startswith(arg.lower())) or (len(arg) > 1 and arg.lower() in mon["index"]):
            names.append(mon["index"])
    if len(names) == 0:
        await ctx.send("Not found.")
        return
    if len(names) > 1:
        await ctx.send("\n".join(names))
        return
    url = "https://www.dnd5eapi.co/api/magic-items/"+names[0]
    res = requests.get(url)
    data = res.json()
    if "error" in data.keys():
        await ctx.send(data["error"])
        return
    embed=Embed(title=data["name"], color=0x109319)
    embed.set_author(name=data["equipment_category"]["name"])
    if "desc" in data.keys():
        embed.add_field(name="Description", value="\n".join(data["desc"]), inline=False) 
    if "cost" in data.keys():
        embed.add_field(name=data["cost"]["unit"], value=data["cost"]["quantity"], inline=True) 
    #embed.set_footer(text=data["description"])
    await ctx.send(embed=embed)

@bot.command(name='class', help="look up 5e player class", pass_context=True)
async def getclass(ctx, arg):
    url = "https://www.dnd5eapi.co/api/classes"
    res = requests.get(url)
    data = res.json()
    l = data["results"]
    names = []
    for mon in l:
        if (len(arg) < 2 and mon["index"].startswith(arg.lower())) or (len(arg) > 1 and arg.lower() in mon["index"]):
            names.append(mon["index"])
    if len(names) == 0:
        await ctx.send("Not found.")
        return
    if len(names) > 1:
        await ctx.send("\n".join(names))
        return
    url = "https://www.dnd5eapi.co/api/classes/"+names[0]
    res = requests.get(url)
    data = res.json()
    if "error" in data.keys():
        await ctx.send(data["error"])
        return
    embed=Embed(title=data["name"], color=0x109319)

    embed.set_author(name="Hit Die: "+str(data["hit_die"]))

    if "subclasses" in data.keys():
        profs = []
        for prof in data["subclasses"]:
            profs.append(prof["name"])
        embed.add_field(name="Subclasses", value="_ "+"_ "+"\n".join(profs), inline=False) 

    if "spellcasting" in data.keys():
        embed.add_field(name="Spellcasting Ability", value="_ "+"_ "+data["spellcasting"]["spellcasting_ability"]["name"], inline=False) 
        for prof in data["spellcasting"]["info"]:
            embed.add_field(name=prof["name"], value="_ "+"_ "+"\n".join(prof["desc"]), inline=False) 

    if "multi_classing" in data.keys():
        profs = []
        prereqs = []
        for prereq in data["multi_classing"]["prerequisites"]:
            prereqs.append(prereq["ability_score"]["name"]+": "+str(prereq["minimum_score"]))
        for prof in data["multi_classing"]["proficiencies"]:
            profs.append(prof["name"])
        embed.add_field(name="Multiclass Prerequisites", value="_ "+"_ "+"\n".join(prereqs), inline=True) 
        embed.add_field(name="Multiclass Proficiencies", value="_ "+"_ "+"\n".join(profs), inline=True) 

    if "saving_throws" in data.keys():
        profs = []
        for prof in data["saving_throws"]:
            profs.append(prof["name"])
        embed.add_field(name="Saving Throws", value="_ "+"_ "+", ".join(profs), inline=False) 

    if "proficiencies" in data.keys():
        profs = []
        for prof in data["proficiencies"]:
            profs.append(prof["name"])
        embed.add_field(name="Proficiencies", value="_ "+"_ "+"\n".join(profs), inline=False) 

    if "starting_equipment" in data.keys():
        sequip = []
        for se in data["starting_equipment"]:
            qty = 1
            if "quantity" in se.keys():
                qty = se["quantity"]
            name = se["equipment"]["name"]
            sequip.append(str(qty)+" x "+name)
        embed.add_field(name="Chose ", value="_ "+"_ "+"\n".join(sequip), inline=False) 

    if "proficiency_choices" in data.keys():
        for pc in data["proficiency_choices"]:
            choose = pc["choose"]
            profs = []
            for prof in pc["from"]:
                profs.append(prof["name"])
            embed.add_field(name="Chose "+str(choose), value="_ "+"_ "+"\n".join(profs), inline=False) 

    if "starting_equipment_options" in data.keys():
        for pc in data["starting_equipment_options"]:
            choose = pc["choose"]
            profs = []
            for prof in pc["from"]:
                if "" in prof.keys():
                    qty = 1
                    if "quantity" in prof.keys():
                        qty = prof["quantity"]
                    name = prof["equipment"]["name"]
                    profs.append(str(qty)+" x "+name)
                if "equipment_option" in prof.keys():
                    profs.append(str(prof["equipment_option"]["choose"])+" x "+prof["equipment_option"]["from"]["equipment_category"]["name"])
            embed.add_field(name="Chose "+str(choose), value="_ "+"_ "+"\n".join(profs), inline=False) 

    if "info" in data.keys():
        for info in data["info"]:
            embed.add_field(name=info["name"], value="_ "+"_ "+info["desc"], inline=False) 

    #embed.set_footer(text=data["description"])
    await ctx.send(embed=embed)

@bot.command(name='map', help='generates a map')
async def mapgen(ctx, *args):
    await ctx.send("This will take a minute or two...")
    mapgen = MapGenerator()
    towns = 3
    if len(args) > 0:
        towns = int(args[0])
    mapgen.create_big_map(towns)
    await ctx.send(file=File('tmap.png'))

@bot.command(name='update', help='update bot source code and restart')
async def update(ctx):
    await ctx.send("Getting source changes.")
    result = subprocess.check_output(["git", "pull"]).decode("utf-8")
    await ctx.send(result)
    time.sleep(10)
    await ctx.send("I am restarting for updates.")
    subprocess.call(["python3", "bot.py"])
    try:
        main_loop.stop()
    except:
        pass
    try:
        bot.close()
    except:
        pass
    exit()

if __name__ == "__main__":
    main_loop.start()
    bot.run(TOKEN)