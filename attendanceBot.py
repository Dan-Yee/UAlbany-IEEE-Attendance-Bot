from ntpath import join
import discord
from discord import user

intents = discord.Intents.default()
intents.members = True
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument, CommandNotFound

import os                                                                                                       
from dotenv import load_dotenv, find_dotenv
import datetime                                                                                                 # used to get timestamp at a given moment
import pandas                                                                                                   # used to calculate the average of datetime's

"""
Class to represent a user on Discord and store join times and leave times
"""
class DiscordUser:
    def __init__(self, userIDNumber: int):
        self.userIDNumber = userIDNumber
        self.joinTimes = list()
        self.leaveTimes = list()

isListening = False                                                                                             # is the bot listening to attendance right now
channelName = None                                                                                              # name of voice channel being listened to
recordedUsers = dict()                                                                                          # accumulation of recorded users in a dictionary
IEEEKnownUsers = dict()                                                                                         # dictionary to track previously seen users before to improve runtime for getting nicknames
attendanceData = None                                                                                           # instantiate global for data file use later
startTime = None                                                                                                # date-time stamp of when #start was run
stopTime = None                                                                                                 # date-time stamp of when #stop was run

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

load_dotenv(find_dotenv())
TOKEN = os.environ.get('BOT_TOKEN')

activity = discord.Activity(type = discord.ActivityType.listening, name = "#start")
bot = commands.Bot(command_prefix = "#", activity = activity, status = discord.Status.online, intents = intents)
bot.remove_command("help")

"""
Event the notify the user of an unknown command being used
"""
@bot.event
async def on_command_error(ctx, error):
    if(isinstance(error, CommandNotFound)):
        await ctx.send("Unknown command")
        await ctx.send("Valid commands are: start, stop, get, whitelist, unwhitelist")

"""
Logs the attendance data whenever someone joins or leaves the specific voice channel, ignoring other voice state updates
"""
@bot.event
async def on_voice_state_update(member, before, after):
    global recordedUsers

    if(isListening):
        joinTime = datetime.datetime.now()
        leaveTime = datetime.datetime.now()

        # if before channel is the same as after channel, some other* voice state was changed (* other voice states are: mute, deaf, self_mute, self_deaf, and others)
        if((str(before.channel).upper() != str(after.channel).upper())):
            if(str(after.channel).upper() == channelName):                                                      # user joined specific channel
                if(recordedUsers.get(member.id) is not None):
                    recordedUsers[member.id].joinTimes.append(joinTime)
                else:
                    recordedUsers[member.id] = DiscordUser(member.id)
                    recordedUsers[member.id].joinTimes.append(joinTime)
            elif(str(before.channel).upper() == channelName):                                                   # user left or switched out of specific channel
                recordedUsers[member.id].leaveTimes.append(leaveTime)                                                           

"""
Starts listening for attendance on a specified channel
"""
@bot.command(name = "start")
async def start(ctx, *, channel):
    global channelName
    global isListening
    global attendanceData
    global startTime

    if(ctx.author.id in whitelistedUsers):                                                                      # check for permission
        if(not isListening):
            channelName = channel.upper()
            listeningChannel = bot.get_channel(IEEEVoiceChannels.get(channelName))
            startTime = datetime.datetime.now()
            attendanceData = open("attendance.txt", "w")

            if(listeningChannel is not None):
                isListening = True

                joinTime = datetime.datetime.now()
                for user in listeningChannel.members:                                                           # Records users already in channel before #start command was run
                    recordedUsers[user.id] = DiscordUser(user.id)
                    recordedUsers[user.id].joinTimes.append(joinTime)

                await ctx.send("Listening for attendance in voice channel: {}".format(channel.title()))
                await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = "attendance"))
            else:
                await ctx.send("Voice channel, {}, not found!".format(channel.title()))
        else:
            await ctx.send("Listening already in progress in voice channel: {}".format(channelName.title()))
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
    global IEEEKnownUsers

    if(ctx.author.id in whitelistedUsers):                                                                      # checks for permission
        if(isListening):
            stopTime = datetime.datetime.now()

            attendanceData.write("Attendance Data for: " + title + "\n")                                        # writes attendance header data
            attendanceData.write("Voice Channel: " + channelName.title() + "\n")
            attendanceData.write("\nStart Time: " + str(startTime) + "\n")
            attendanceData.write("Stop Time: " + str(stopTime) + "\n")
            attendanceData.write("Total Runtime: " + str(stopTime - startTime) + "\n")
            attendanceData.write("Attendance Count: " + str(len(recordedUsers)) + "\n")
            attendanceData.write("\n==================================================\n")

            for entry in recordedUsers.values():                                                                # writes each record of data to file
                attendanceData.write("Member: " + str(bot.get_user(entry.userIDNumber)) + "\n")

                if(IEEEKnownUsers.get(entry.userIDNumber) is not None):                                         # optimize by checking a dictionary of previously recorded members
                    attendanceData.write("Nickname: " + str(IEEEKnownUsers.get(entry.userIDNumber)) + "\n\n")
                else:                                                                                           # loop through all members of "UAlbany IEEE" server to find user nickname
                    for member in bot.get_guild(685303775052693515).members:
                        if(member.id == entry.userIDNumber):
                            attendanceData.write("Nickname: " + str(member.display_name) + "\n\n")
                            IEEEKnownUsers[entry.userIDNumber] = str(member.display_name)
                            break

                attendanceData.write("Join Time(s):\n")
                for joinTime in entry.joinTimes:
                    attendanceData.write("\t" + str(joinTime) + "\n")
                attendanceData.write("Leave Time(s):\n")

                if((len(entry.leaveTimes) == 0) or (len(entry.joinTimes) > len(entry.leaveTimes))):             # automatically append an leave time if the user never left since the bot stopped listening
                    recordedUsers[entry.userIDNumber].leaveTimes.append(stopTime)                               # if join list is longer than leave list, user has disconnected and reconnected but didn't leave before the bot stopped listening

                for leaveTime in entry.leaveTimes:
                    attendanceData.write("\t" + str(leaveTime) + "\n")

                joinTimeAvg = pandas.Series(entry.joinTimes).mean()                                             # calculate averages of join and leave times for more accurate estimated attendance
                leaveTimeAvg = pandas.Series(entry.leaveTimes).mean()
                
                attendanceData.write("\nEstimated Attendance Time: " + str(leaveTimeAvg - joinTimeAvg)[7:22] + "\n")
                attendanceData.write("==================================================\n")
            
            isListening = False
            channelName = ""
            recordedUsers.clear()
            attendanceData.close()

            await ctx.send("Attendance data saved as: {}".format(title))
            await ctx.send("Attendance data sent to {}".format(ctx.author.mention))

            with open("attendance.txt", "rb") as file:                                                          # sends the file to the author who ran the command through DM
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
    if(ctx.author.id in whitelistedUsers):                                                                      # checks for permission
        with open("attendance.txt", "rb") as file:                                                              # sends the most recent file to the author who ran the command through DM
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

    if(ctx.author.id in whitelistedUsers):                                                                      # checks for permission
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

    if(ctx.author.id in whitelistedUsers):                                                                      # checks for permission
        if(bot.get_user(int(userID)) is not None):
            if(int(userID) not in whitelistedUsers):
                await ctx.send("{} is not on the whitelist".format(bot.get_user(int(userID))))
            elif(str(ctx.author.id) == userID.strip()):
                await ctx.send("You cannot remove yourself from the whitelist")
            elif(str(274354935036903424) == userID.strip() or str(224552342438150144) == userID.strip()):       # Special Case: Cannot remove two users: Server Owner and Bot Author
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