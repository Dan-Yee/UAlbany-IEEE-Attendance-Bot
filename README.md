# IEEE Attendance Discord Bot

A Discord bot that is used to take attendance of events/workshops held on Discord by date-time stamping when a user joins or leaves a specific voice channel if it exists

Commands:
- #start [voice channel name] - the bot will start listening for attendance on the specified channel name if it can be found
- #stop [event title] - the bot will stop listening for attendance, write the data to a .txt file and send it to the person who ran the command through a direct message
- #get - the bot will send the most recent attendance data file to the person who ran the command through a direct message
- #add [user id] - adds a user to the whitelist, giving them permission to run bot commands
- #remove [user id] - removes a user from the whitelist, removing their permission to run bot commands
