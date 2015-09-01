LOL-ItemSets
===================

This program acts as a webapp, which will display the past 5 weeks of games from a few Pro League of Legends regions. Users can then select a particular game they're interested in, and select a player to download that particular item build.

If you're just interested in seeing what it looks like, check out this youtube video to get a demonstration (I recommend muting):
http://youtu.be/ze_MWHqlPeI

----------


How To Run
-------------

This program requires two things to run:

1. The 2.7 branch of Python
2. Flask, the microframework server for Python.

Once you obtain the two, running is done by opening a command terminal and entering the following:

    > python lolitemsets.py

Once that's done, you can access the site via localhost:5000. 

How To Set Up The Database
-------------

The database is currently already set up, but if you wanted to change either the type of data the database holds, or add more matches, here's what you need to do.

Before you do anything, you'll need to have an API key set up for the program. You can go to Riot's official API to get a key. Once you've obtained a key, create a file called configuration. No .txt, just configuration. Inside the file, write the following:

		[Riot API]
		SECRET_KEY = your-key-goes-here

Once you've done this, you can now initialize the database.

1. If you're just adding more matches, all you need to do is run python in command prompt. Once you do so, write the following commands:
    
		from lolitemsets import add_matches
	    add_match()

    >Note: This is super bad and mean to Riot's database, don't do this.

2. If you're looking to change the database format, you will need to change the schema.sql file, and then you will need to reinitialize the database. To reinitialize the database, type the following after running python in your command prompt:
		
		from lolitemsets import init_db
		init_db()
Once you initialize the database, you will have champions and items in it, but no matches. You'll have to call add_matches as described above.

Remember guys, Pro-Item-Sets isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing League of Legends. League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc. League of Legends © Riot Games, Inc.
