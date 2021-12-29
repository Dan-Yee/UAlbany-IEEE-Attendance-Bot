import discord
from discord import user
intents = discord.Intents.default()
intents.members = True

from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument

import os
from dotenv import load_dotenv, find_dotenv

import datetime

isListening = False
channelName = ""
recordedUsers = []
attendanceData = ""
startTime = ""
stopTime = ""

IEEEVoiceChannels = {
    "PRESENTATION" : 693685771865161778,
    "CODING NIGHT" : 795816903837745152,
    "PROJECT DEVELOPMENT VOICE" : 771886074456702976,
    "OFFICERS VOICE" : 685319023256141834,
    "EBOARD VOICE" : 903111739892199486,
    "BRUH" : 912561278575329326
}

whitelistedUsers = {
    274354935036903424,
    224552342438150144
}

"""
Class to represent a user on Discord and store join times and leave times
"""
class DiscordUser:
    def __init__(self, userIDNumber: int):
        self.userIDNumber = userIDNumber
        self.joinTimes = []
        self.leaveTimes = []

load_dotenv(find_dotenv())
TOKEN = os.environ.get('BOT_TOKEN')

activity = discord.Activity(type = discord.ActivityType.listening, name = "#start")
bot = commands.Bot(command_prefix = "#", activity = activity, status = discord.Status.online, intents = intents)
bot.remove_command("help")

"""
Logs the attendance data whenever someone joins or leaves
"""
@bot.event
async def on_voice_state_update(member, before, after):
    global recordedUsers
    isNewRecord = False
    recordIndex = 0
    joinTime = str(datetime.datetime.now())

    if(isListening):
        if(str(after.channel).upper() == channelName):                                              # user joined specific channel
            if(len(recordedUsers) != 0):                                                            # case if the voice channel was empty when the command was run
                for user in recordedUsers:                                                          # checks if user record already exists
                    if(user.userIDNumber != member.id):
                        isNewRecord = True
                    else:
                        recordIndex = recordedUsers.index(user)
                        isNewRecord = False
                        break
            else:
                isNewRecord = True;

            if(isNewRecord):                                                                        # creates a new record for the user and notes their join time
                recordedUsers.append(DiscordUser(member.id))
                recordedUsers[len(recordedUsers) - 1].joinTimes.append(joinTime)
                isNewRecord = False
            else:
                recordedUsers[recordIndex].joinTimes.append(joinTime)
        elif(str(before.channel).upper() == channelName and after.channel is None):                 # user left specific channel
            leaveTime = str(datetime.datetime.now())

            for user in recordedUsers:
                if(user.userIDNumber == member.id):
                    user.leaveTimes.append(leaveTime)
                    break                                                              

"""
Starts listening for attendance on a specified channel
"""
@bot.command(name = "start")
async def start(ctx, *, channel):
    global channelName
    global isListening
    global attendanceData
    global startTime

    if(ctx.author.id in whitelistedUsers):
        if(not isListening):
            channelName = channel.upper()
            listeningChannel = bot.get_channel(IEEEVoiceChannels.get(channelName))
            startTime = datetime.datetime.now()
            attendanceData = open("attendance.txt", "w")

            if(listeningChannel is not None):
                isListening = True

                # Records users already in channel before #start command was run
                for user in listeningChannel.members:
                    recordedUsers.append(DiscordUser(user.id))
        
                joinTime = str(datetime.datetime.now())
                for user in recordedUsers:
                    user.joinTimes.append(joinTime)

                await ctx.send("Listening for attendance in Voice Channel: {}".format(channel))
                await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = "attendance"))
            else:
                await ctx.send("Voice Channel, {}, not found!".format(channel))
        else:
            await ctx.send("Listening already in progress in Voice Channel: {}".format(channel))
    else:
        await ctx.send("Permission denied")

@start.error
async def startError(ctx, error):
    if(isinstance(error, MissingRequiredArgument)):
        await ctx.send("Missing argument in: #start [voice channel name]") 

"""
Stops the bot from listening and sends the attendance data to the author if they have permission
"""
@bot.command(name = "stop")
async def stop(ctx, *, title):
    global isListening
    global channelName
    global recordedUsers
    global attendanceData
    global startTime
    global stopTime
    
    if(ctx.author.id in whitelistedUsers):
        if(isListening):
            isListening = False
            channelName = ""
            stopTime = datetime.datetime.now()

            attendanceData.write("Attendance Data for: " + title + "\n")
            attendanceData.write("Start Time: " + str(startTime) + "\n")
            attendanceData.write("Stop Time: " + str(stopTime) + "\n")
            attendanceData.write("Total Runtime: " + str(stopTime - startTime) + "\n")
            attendanceData.write("\n==================================================\n")

            for entry in recordedUsers:
                attendanceData.write("Member: " + str(bot.get_user(entry.userIDNumber)) + "\n")
                attendanceData.write("Join Times:\n")
                for joinTime in entry.joinTimes:
                    attendanceData.write("\t" + str(joinTime) + "\n")
                attendanceData.write("Leave Times:\n")
                for leaveTime in entry.leaveTimes:
                    attendanceData.write("\t" + str(leaveTime) + "\n")
                if(len(entry.leaveTimes) == 0):
                    attendanceData.write("\t" + str(stopTime) + "\n")
                attendanceData.write("==================================================\n")
            
            recordedUsers.clear()
            attendanceData.close()

            await ctx.send("Attendance data saved as: {}".format(title))
            await ctx.send("Attendance data sent to {}".format(ctx.author.mention))

            with open("attendance.txt", "rb") as file:
                await ctx.author.send("Attendance File: ", file = discord.File(file, "attendance.txt"))
                file.close()
            await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = "#start"))
        else:
            await ctx.send("Listening was never started!")
    else:
        await ctx.send("Permission denied")

@stop.error
async def stopError(ctx, error):
    if(isinstance(error, MissingRequiredArgument)):
        await ctx.send("Missing argument in: #stop [event title]")

"""
Sends the most recent attendance data file to the command author if they have permission
"""
@bot.command(name = "get")
async def get(ctx):
    if(ctx.author.id in whitelistedUsers):
        with open("attendance.txt", "rb") as file:
            await ctx.send("Attendance data sent to {}".format(ctx.author.mention))
            await ctx.author.send("Attendance File: ", file = discord.File(file, "attendance.txt"))
            file.close()
    else:
        await ctx.send("Permission denied")

"""
Give a user permission to run bot commands
"""
@bot.command(name = "whitelist")
async def whitelist(ctx, userID):
    global whitelistedUsers

    if(ctx.author.id in whitelistedUsers):
        if(int(userID) in whitelistedUsers):
            await ctx.send("{} is already whitelisted".format(bot.get_user(int(userID))))
        elif(bot.get_user(int(userID)) is not None):
            whitelistedUsers.add(int(userID))
            await ctx.send("{} was whitelisted".format(bot.get_user(int(userID))))
        else:
            await ctx.send("Invalid User ID")
    else:
        await ctx.send("Permission denied")

@whitelist.error
async def whitelistError(ctx, error):
    if(isinstance(error, MissingRequiredArgument)):
        await ctx.send("Missing argument in: #whitelist [user id]")

"""
Remove a users permission to run bot commands
"""
@bot.command(name = "unwhitelist")
async def unwhitelist(ctx, userID):
    global whitelistedUsers

    if(ctx.author.id in whitelistedUsers):
        if(bot.get_user(int(userID)) is not None):
            if(int(userID) not in whitelistedUsers):
                await ctx.send("{} is not in the whitelist".format(bot.get_user(int(userID))))
            elif(str(ctx.author.id) == userID.strip()):
                await ctx.send("You cannot remove yourself from the whitelist")
            elif(str(274354935036903424) == userID.strip() or str(224552342438150144) == userID.strip()):
                await ctx.send("{} cannot be removed from the whitelist".format(bot.get_user(int(userID))))
            else:
                whitelistedUsers.remove(int(userID))
                await ctx.send("{} was removed from the whitelist".format(bot.get_user(int(userID))))
        else:
            await ctx.send("Invalid User ID")
    else:
        await ctx.send("Permission denied")

@unwhitelist.error
async def unwhitelistError(ctx, error):
    if(isinstance(error, MissingRequiredArgument)):
        await ctx.send("Missing argument in: #unwhitelist [user id]")

bot.run(TOKEN)