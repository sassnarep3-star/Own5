#!/usr/bin/env python3
"""Capture script: official NFL Week 10 2026 injury report, transcribed verbatim.

Source: https://www.nfl.com/injuries/league/2026/reg10  (page title: "Week 10 of the 2026 Season")
Read through the sandbox page fetcher on 2026-11-15, all 8 chunks, at 23:25Z.

Rules applied while transcribing (no inference anywhere):
  * "Practice Status" is recorded exactly as published (full text).
  * "Game Status" is recorded exactly as published. Where the cell is empty it is
    written as the literal token BLANK. BLANK is *not* a designation and is never
    counted as one.
  * "Injuries" (the description cell) is recorded exactly as published; empty -> BLANK.
  * No row is added, removed or reordered within a club. Clubs appear in page order.
  * Only the 28 clubs playing in Week 10 appear (CHI, DEN, PHI, TB are on bye).

Output: data/injuries_wk10.csv and data/injuries_wk10_summary.csv
"""
import csv
import os

SRC = "https://www.nfl.com/injuries/league/2026/reg10"
FETCHED = "2026-11-15T23:25:00Z"
WEEK = "10"

FULL = "Full Participation in Practice"
LIM = "Limited Participation in Practice"
DNP = "Did Not Participate In Practice"
B = "BLANK"

# (club, player, position, injury_description, practice_status, game_status, chunk)
ROWS = [
    # ---- WAS @ NYG (Thursday, November 12) -- chunk 0
    ("WAS", "John Bates", "TE", B, FULL, B, 0),
    ("WAS", "Treylon Burks", "WR", B, DNP, B, 0),
    ("WAS", "Jayden Daniels", "QB", B, FULL, B, 0),
    ("WAS", "Matt Gulbin", "C", B, FULL, B, 0),
    ("WAS", "Chig Okonkwo", "TE", B, FULL, B, 0),
    ("WAS", "Lucas Patrick", "C", "Concussion", DNP, "Out", 0),
    ("WAS", "Amik Robertson", "CB", B, LIM, B, 0),
    ("WAS", "Shy Tuttle", "DT", B, FULL, B, 0),
    ("WAS", "Colson Yankoff", "TE", "Knee", DNP, "Out", 0),
    ("NYG", "Abdul Carter", "LB", B, FULL, B, 0),
    ("NYG", "Jermaine Eluemunor", "T", B, FULL, B, 0),
    ("NYG", "Malik Harrison", "LB", "Groin", LIM, "Questionable", 0),
    ("NYG", "Colton Hood", "CB", B, FULL, B, 0),
    ("NYG", "Theo Johnson", "TE", B, FULL, B, 0),
    ("NYG", "Charlie Jones", "WR", B, FULL, B, 0),
    ("NYG", "J.J. McCarthy", "QB", B, FULL, B, 0),
    ("NYG", "Darnell Mooney", "WR", B, FULL, B, 0),
    ("NYG", "Malik Nabers", "WR", B, FULL, B, 0),
    ("NYG", "Cam Skattebo", "RB", B, FULL, B, 0),
    ("NYG", "Andrew Thomas", "T", B, FULL, B, 0),
    # ---- NE @ DET (Sunday, November 15, 9:30 AM) -- chunk 0
    ("NE", "Ben Brown", "C", "Knee", DNP, "Out", 0),
    ("NE", "A.J. Brown", "WR", "Ankle, Knee", LIM, "Questionable", 0),
    ("NE", "Kevin Byard", "S", "Chest", FULL, "Questionable", 0),
    ("NE", "Carlton Davis III", "CB", "Knee", DNP, "Out", 0),
    ("NE", "Reggie Gilliam", "FB", "Knee", LIM, "Questionable", 0),
    ("NE", "TreVeyon Henderson", "RB", "Illness", DNP, "Out", 0),
    ("NE", "Hunter Henry", "TE", B, LIM, B, 0),
    ("NE", "Cameron Latu", "TE", "Back", LIM, "Questionable", 0),
    ("NE", "Drake Maye", "QB", B, FULL, B, 0),
    ("NE", "Morgan Moses", "T", B, FULL, B, 0),
    ("NE", "Walter Rouse", "T", "Concussion", LIM, "Questionable", 0),
    ("NE", "Brenden Schooler", "S", "Hamstring", LIM, "Questionable", 0),
    ("NE", "Rhamondre Stevenson", "RB", "Knee", LIM, "Questionable", 0),
    ("NE", "Greg Van Roten", "G", "Hamstring", FULL, "Questionable", 0),
    ("NE", "Charles Woods", "CB", "Hamstring", FULL, "Questionable", 0),
    ("DET", "Brian Branch", "S", B, FULL, B, 0),
    ("DET", "Jared Goff", "QB", B, FULL, B, 0),
    ("DET", "Kerby Joseph", "S", "Knee", DNP, "Out", 0),
    ("DET", "Cade Mays", "C", "Ankle", DNP, "Out", 0),
    ("DET", "D.J. Reed", "CB", "Hip", DNP, "Out", 0),
    ("DET", "Jacob Saylors", "RB", B, FULL, B, 0),
    ("DET", "Amon-Ra St. Brown", "WR", "Rib", LIM, "Questionable", 0),
    ("DET", "Sione Vaki", "RB", "Ankle", LIM, "Questionable", 0),
    ("DET", "DJ Wonnum", "DE", B, FULL, B, 0),
    # ---- KC @ ATL (1:00 PM) -- chunks 0/1
    ("KC", "Jeffrey Bassa", "LB", B, FULL, B, 0),
    ("KC", "Mansoor Delane", "CB", "Shoulder", FULL, "Questionable", 0),
    ("KC", "Justin Fields", "QB", B, FULL, B, 0),
    ("KC", "Jaden Hicks", "S", B, FULL, B, 0),
    ("KC", "Travis Kelce", "TE", B, FULL, B, 0),
    ("KC", "Patrick Mahomes", "QB", B, FULL, B, 0),
    ("KC", "Jaylon Moore", "T", "Ankle", DNP, "Out", 1),
    ("KC", "Omarr Norman-Lott", "DT", "Knee", LIM, "Out", 1),
    ("KC", "Jaydn Ott", "RB", "Hamstring", LIM, "Questionable", 1),
    ("KC", "Rashee Rice", "WR", B, FULL, B, 1),
    ("KC", "Kenneth Walker III", "RB", "Groin", DNP, "Questionable", 1),
    ("KC", "Peter Woods", "DT", "Neck", DNP, "Out", 1),
    ("KC", "Xavier Worthy", "WR", B, FULL, B, 1),
    ("ATL", "Zachariah Branch", "WR", "Hamstring", DNP, "Out", 1),
    ("ATL", "Kendal Daniels", "LB", B, FULL, B, 1),
    ("ATL", "Divine Deablo", "LB", "Forearm", DNP, "Doubtful", 1),
    ("ATL", "Gervon Dexter Sr.", "DT", "Illness", LIM, "Questionable", 1),
    ("ATL", "Jake Matthews", "T", B, LIM, B, 1),
    ("ATL", "Liam McCullough", "LS", B, DNP, B, 1),
    ("ATL", "James Pearce Jr.", "DE", "Back", LIM, "Questionable", 1),
    ("ATL", "Za'Darius Smith", "DE", B, FULL, B, 1),
    ("ATL", "Jawaan Taylor", "T", B, LIM, B, 1),
    ("ATL", "Cameron Thomas", "DE", B, FULL, B, 1),
    ("ATL", "Josh Woods", "LB", "Ankle", FULL, "Questionable", 1),
    # ---- MIN @ GB (1:00 PM) -- chunk 1
    ("MIN", "Jordan Addison", "WR", "Thumb", LIM, "Questionable", 1),
    ("MIN", "Blake Cashman", "LB", "Concussion", LIM, "Out", 1),
    ("MIN", "Christian Darrisaw", "T", B, DNP, B, 1),
    ("MIN", "T.J. Hockenson", "TE", "Wrist, Chest", DNP, "Out", 1),
    ("MIN", "Tyrion Ingram-Dawkins", "DT", "Ankle", DNP, "Out", 1),
    ("MIN", "Theo Jackson", "S", B, FULL, B, 1),
    ("MIN", "Jauan Jennings", "WR", "Calf", DNP, "Out", 1),
    ("MIN", "Josh Metellus", "S", "Shoulder", LIM, "Questionable", 1),
    ("MIN", "Kyler Murray", "QB", "Hamstring", DNP, "Out", 1),
    ("MIN", "Harrison Smith", "S", B, LIM, B, 1),
    ("MIN", "Kyle Van Noy", "LB", "Calf", LIM, "Questionable", 1),
    ("MIN", "Jay Ward", "S", B, FULL, B, 1),
    ("MIN", "Carson Wentz", "QB", B, FULL, B, 1),
    ("GB", "Aaron Banks", "G", B, LIM, B, 1),
    ("GB", "Chris Brooks", "RB", "Ankle", LIM, "Questionable", 1),
    ("GB", "Javon Bullard", "S", "Ankle, Knee", LIM, "Questionable", 1),
    ("GB", "Zaire Franklin", "LB", "Shin", DNP, "Doubtful", 1),
    ("GB", "Travis Glover", "G", "Knee", LIM, "Questionable", 1),
    ("GB", "Ty'Ron Hopper", "LB", B, FULL, B, 1),
    ("GB", "Josh Jacobs", "RB", "Finger", DNP, "Out", 1),
    ("GB", "Xavier McKinney", "S", "Foot", LIM, "Questionable", 1),
    ("GB", "Bo Melton", "WR", B, FULL, B, 1),
    ("GB", "Skyy Moore", "WR", "Ankle", LIM, "Questionable", 1),
    ("GB", "Micah Parsons", "LB", "Knee, Illness", LIM, "Out", 1),
    ("GB", "Sean Rhyan", "C", "Ankle", DNP, "Out", 1),
    ("GB", "Trey Smack", "K", B, FULL, B, 1),
    ("GB", "Lukas Van Ness", "LB", "Back", LIM, "Questionable", 1),
    ("GB", "Josh Whyle", "TE", "Concussion", DNP, "Out", 1),
    ("GB", "Savion Williams", "WR", B, LIM, B, 1),
    ("GB", "Kevin Zeitler", "G", "Ankle, Triceps", DNP, "Questionable", 1),
    # ---- JAX @ TEN (1:00 PM) -- chunks 1/2
    ("JAX", "Jessie Bates", "S", "Not injury related - resting player", LIM, "Out", 1),
    ("JAX", "Ezra Cleveland", "G", B, FULL, B, 1),
    ("JAX", "Branson Combs", "LB", B, FULL, B, 1),
    ("JAX", "Jordan Davis", "DT", "Not injury related - resting player", LIM, "Out", 1),
    ("JAX", "BJ Green II", "DE", "Forearm", FULL, "Out", 1),
    ("JAX", "Robert Hainsey", "C", "Concussion", LIM, "Questionable", 1),
    ("JAX", "Antonio Johnson", "S", B, LIM, B, 1),
    ("JAX", "Jakobi Meyers", "WR", B, LIM, B, 1),
    ("JAX", "Chris Rodriguez Jr.", "RB", B, LIM, B, 1),
    ("JAX", "Bhayshul Tuten", "RB", B, LIM, B, 2),
    ("JAX", "Travon Walker", "DE", B, LIM, B, 2),
    ("TEN", "Cody Barton", "LB", "Concussion", DNP, "Out", 2),
    ("TEN", "John Franklin-Myers", "DE", B, FULL, B, 2),
    ("TEN", "Marcus Harris", "CB", B, FULL, B, 2),
    ("TEN", "Anthony Hill Jr.", "LB", "Neck", DNP, "Out", 2),
    ("TEN", "Jaylon Jones", "CB", B, FULL, B, 2),
    ("TEN", "JC Latham", "T", B, FULL, B, 2),
    ("TEN", "Tony Pollard", "RB", B, FULL, B, 2),
    ("TEN", "Peter Skoronski", "G", "Hamstring", DNP, "Out", 2),
    ("TEN", "Tyjae Spears", "RB", "Knee", FULL, "Questionable", 2),
    ("TEN", "Carnell Tate", "WR", "Shoulder", DNP, "Out", 2),
    ("TEN", "Tommy Townsend", "P", "Knee, Achilles", DNP, "Out", 2),
    ("TEN", "Kevin Winston Jr.", "S", B, FULL, B, 2),
    # ---- BUF @ NYJ (1:00 PM) -- chunk 2
    ("BUF", "Alec Anderson", "G", B, FULL, B, 2),
    ("BUF", "Christian Benford", "CB", "Wrist", FULL, "Questionable", 2),
    ("BUF", "Terrel Bernard", "LB", B, DNP, B, 2),
    ("BUF", "Spencer Brown", "T", "Ankle", DNP, "Doubtful", 2),
    ("BUF", "Dion Dawkins", "T", B, FULL, B, 2),
    ("BUF", "Sam Franklin Jr.", "S", "Shoulder", LIM, "Questionable", 2),
    ("BUF", "Greg Gaines", "DT", B, FULL, B, 2),
    ("BUF", "Jordan Hancock", "CB", "Hamstring", FULL, "Questionable", 2),
    ("BUF", "Dalton Kincaid", "TE", B, FULL, B, 2),
    ("BUF", "Connor McGovern", "C", B, FULL, B, 2),
    ("BUF", "Ed Oliver", "DE", B, DNP, B, 2),
    ("BUF", "Ar'maj Reed-Adams", "G", B, FULL, B, 2),
    ("BUF", "T.J. Sanders", "DE", B, FULL, B, 2),
    ("BUF", "Tyrell Shavers", "WR", "Knee", FULL, "Questionable", 2),
    ("NYJ", "Jarvis Brownlee Jr.", "CB", "Illness", LIM, "Questionable", 2),
    ("NYJ", "Omar Cooper Jr.", "WR", "Ankle", FULL, "Questionable", 2),
    ("NYJ", "Adonai Mitchell", "WR", "Knee", FULL, "Questionable", 2),
    ("NYJ", "Joseph Ossai", "DE", "Ankle", FULL, "Questionable", 2),
    ("NYJ", "VJ Payne", "S", "Knee", FULL, "Questionable", 2),
    ("NYJ", "Harrison Phillips", "DT", "Ankle", FULL, "Questionable", 2),
    ("NYJ", "Trevin Wallace", "LB", "Groin", DNP, "Out", 2),
    ("NYJ", "Garrett Wilson", "WR", "Concussion", FULL, "Questionable", 2),
    ("NYJ", "Nahshon Wright", "CB", "Back", FULL, "Questionable", 2),
    # ---- MIA @ IND (1:00 PM) -- chunks 2/3
    ("MIA", "Tucker Addington", "LS", B, LIM, B, 2),
    ("MIA", "Kaytron Allen", "RB", B, FULL, B, 2),
    ("MIA", "Darrell Baker Jr.", "CB", "Knee", FULL, "Questionable", 2),
    ("MIA", "Chris Bell", "WR", "Knee", DNP, "Doubtful", 2),
    ("MIA", "Aaron Brewer", "C", "Concussion", DNP, "Out", 2),
    ("MIA", "Malik Herring", "DE", B, FULL, B, 2),
    ("MIA", "Will Kacmarek", "TE", B, FULL, B, 2),
    ("MIA", "Michael Taaffe", "S", B, FULL, B, 2),
    ("MIA", "Dante Trader Jr.", "S", B, FULL, B, 2),
    ("MIA", "Jared Wayne", "WR", "Quadricep", DNP, "Out", 2),
    ("MIA", "Jaylen Wright", "RB", B, FULL, B, 2),
    ("IND", "Mo Alie-Cox", "TE", "Groin", DNP, "Out", 2),
    ("IND", "CJ Allen", "LB", B, FULL, B, 2),
    ("IND", "Jaylon Carlies", "LB", "Neck", DNP, "Out", 2),
    ("IND", "Akeem Davis-Gaither", "LB", "Knee", DNP, "Out", 2),
    ("IND", "A.J. Haulcy", "S", B, FULL, B, 2),
    ("IND", "Arden Key", "DE", B, FULL, B, 2),
    ("IND", "Will Mallory", "TE", "Hamstring", LIM, "Questionable", 2),
    ("IND", "Luke Rhodes", "LS", "Hamstring", DNP, "Out", 2),
    ("IND", "Grover Stewart", "DT", B, FULL, B, 2),
    ("IND", "Jonathan Taylor", "RB", B, FULL, B, 3),
    ("IND", "Jerry Tillery", "DT", "Calf", DNP, "Out", 3),
    ("IND", "Jalen Travis", "T", "Knee", DNP, "Out", 3),
    ("IND", "Justin Walley", "CB", B, FULL, B, 3),
    ("IND", "Charvarius Ward", "CB", B, FULL, B, 3),
    # ---- CAR @ NO (1:00 PM) -- chunk 3
    ("CAR", "Jonathon Brooks", "RB", "Groin", LIM, "Doubtful", 3),
    ("CAR", "Brady Christensen", "G", "Hamstring", FULL, "Questionable", 3),
    ("CAR", "Trevor Etienne", "RB", B, FULL, B, 3),
    ("CAR", "Chuba Hubbard", "RB", B, FULL, B, 3),
    ("CAR", "Lee Hunter", "DT", B, FULL, B, 3),
    ("CAR", "Mike Jackson", "CB", "Groin", LIM, "Doubtful", 3),
    ("CAR", "Will Lee III", "CB", "Hamstring", LIM, "Questionable", 3),
    ("CAR", "Xavier Legette", "WR", "Knee", FULL, "Questionable", 3),
    ("CAR", "Damien Lewis", "G", B, FULL, B, 3),
    ("CAR", "Bobby Okereke", "LB", "Foot", DNP, "Out", 3),
    ("CAR", "Jaelan Phillips", "LB", "Hamstring", FULL, "Questionable", 3),
    ("CAR", "Torricelli Simpkins III", "G", B, FULL, B, 3),
    ("NO", "Kelvin Banks Jr.", "T", B, FULL, B, 3),
    ("NO", "CJ Donaldson", "RB", "Shoulder", DNP, "Out", 3),
    ("NO", "David Edwards", "G", B, FULL, B, 3),
    ("NO", "Martin Emerson", "CB", "Shin", LIM, "Questionable", 3),
    ("NO", "Travis Etienne", "RB", "Hamstring", FULL, "Questionable", 3),
    ("NO", "Noah Fant", "TE", B, FULL, B, 3),
    ("NO", "Taliese Fuaga", "T", "Knee", DNP, "Out", 3),
    ("NO", "Alvin Kamara", "RB", B, FULL, B, 3),
    ("NO", "Erik McCoy", "C", "Biceps", DNP, "Out", 3),
    ("NO", "Christen Miller", "DT", "Knee", DNP, "Out", 3),
    ("NO", "Asim Richards", "T", B, FULL, B, 3),
    ("NO", "Quincy Riley", "CB", B, FULL, B, 3),
    # ---- HOU @ CLE (1:00 PM) -- chunk 3
    ("HOU", "Azeez Al-Shaair", "LB", "Groin, Not injury related - personal matter", DNP, "Out", 3),
    ("HOU", "Will Anderson Jr.", "DE", "Ankle", DNP, "Questionable", 3),
    ("HOU", "Reed Blankenship", "S", B, FULL, B, 3),
    ("HOU", "Trent Brown", "T", "Wrist, Illness", DNP, "Questionable", 3),
    ("HOU", "Tank Dell", "WR", B, FULL, B, 3),
    ("HOU", "Blake Fisher", "T", B, FULL, B, 3),
    ("HOU", "Marvin Harrison Jr.", "WR", "Hamstring", DNP, "Out", 3),
    ("HOU", "Jacob Hummel", "LB", "Groin", FULL, "Questionable", 3),
    ("HOU", "Danielle Hunter", "DE", "Hamstring", DNP, "Out", 3),
    ("HOU", "Brevin Jordan", "TE", "Finger, Foot", DNP, "Out", 3),
    ("HOU", "Woody Marks", "RB", B, FULL, B, 3),
    ("HOU", "David Montgomery", "RB", "Groin", FULL, "Questionable", 3),
    ("HOU", "Keylan Rutledge", "G", "Neck, Shoulder", DNP, "Out", 3),
    ("HOU", "Jaylin Smith", "CB", "Hamstring", FULL, "Questionable", 3),
    ("HOU", "Wyatt Teller", "G", "Illness, Back", LIM, "Questionable", 3),
    ("HOU", "Tommy Togiai", "DT", B, FULL, B, 3),
    ("CLE", "Austin Barber", "T", B, FULL, B, 3),
    ("CLE", "Denzel Boston", "WR", "Toe", LIM, "Questionable", 3),
    ("CLE", "Michael Burton", "FB", "Calf", DNP, "Out", 3),
    ("CLE", "Maliek Collins", "DT", B, FULL, B, 3),
    ("CLE", "Harold Fannin Jr.", "TE", B, FULL, B, 3),
    ("CLE", "Ronnie Hickman Jr.", "S", "Concussion", DNP, "Out", 3),
    ("CLE", "Tytus Howard", "T", B, FULL, B, 3),
    ("CLE", "Elgton Jenkins", "C", B, FULL, B, 3),
    ("CLE", "Donovan McMillon", "S", B, LIM, B, 3),
    ("CLE", "Carson Schwesinger", "LB", B, FULL, B, 3),
    ("CLE", "Denzel Ward", "CB", B, LIM, B, 3),
    ("CLE", "Quincy Williams", "LB", B, FULL, B, 3),
    # ---- LAR @ AZ (4:05 PM) -- chunk 4
    ("LAR", "Davis Allen", "TE", "Oblique", LIM, "Questionable", 4),
    ("LAR", "Steve Avila", "G", "Hamstring", DNP, "Out", 4),
    ("LAR", "Joe Cardona", "LS", "Ankle", LIM, "Questionable", 4),
    ("LAR", "Kam Curl", "S", "Toe", LIM, "Questionable", 4),
    ("LAR", "Aaron Donald", "DT", B, DNP, B, 4),
    ("LAR", "Terrance Ferguson", "TE", "Ankle, Hamstring", DNP, "Out", 4),
    ("LAR", "Braden Fiske", "DT", B, DNP, B, 4),
    ("LAR", "Myles Garrett", "LB", "Knee, Not injury related - resting player", DNP, "Questionable", 4),
    ("LAR", "Tyler Higbee", "TE", B, LIM, B, 4),
    ("LAR", "Trent McDuffie", "CB", "Back", LIM, "Questionable", 4),
    ("LAR", "Puka Nacua", "WR", B, DNP, B, 4),
    ("LAR", "Colby Parkinson", "TE", B, FULL, B, 4),
    ("LAR", "Matthew Stafford", "QB", B, FULL, B, 4),
    ("LAR", "Byron Young", "LB", B, DNP, B, 4),
    ("AZ", "Budda Baker", "S", B, FULL, B, 4),
    ("AZ", "Zachary Carter", "DT", "Knee", LIM, "Out", 4),
    ("AZ", "Hjalte Froholdt", "C", "Concussion", DNP, "Out", 4),
    ("AZ", "Jon Gaines II", "G", "Ankle", DNP, "Out", 4),
    ("AZ", "Bam Knight", "RB", B, FULL, B, 4),
    ("AZ", "Hunter Long", "TE", "Knee", LIM, "Questionable", 4),
    ("AZ", "Roy Lopez", "DT", "Toe, Ankle", LIM, "Questionable", 4),
    ("AZ", "Max Melton", "CB", "Knee, Hand", LIM, "Questionable", 4),
    ("AZ", "Darius Robinson", "DT", "Wrist", LIM, "Questionable", 4),
    ("AZ", "Isaac Seumalo", "G", B, FULL, B, 4),
    ("AZ", "Dante Stills", "DT", B, FULL, B, 4),
    ("AZ", "Josh Sweat", "LB", B, FULL, B, 4),
    ("AZ", "Jayden Williams", "T", "Knee", LIM, "Questionable", 4),
    ("AZ", "Mack Wilson", "LB", B, FULL, B, 4),
    ("AZ", "Andrew Wingard", "S", "Groin", DNP, "Questionable", 4),
    # ---- SEA @ LV (4:05 PM) -- chunk 4
    ("SEA", "AJ Barner", "TE", B, FULL, B, 4),
    ("SEA", "Anthony Bradford", "G", B, FULL, B, 4),
    ("SEA", "Charles Cross", "T", "Ankle", DNP, "Out", 4),
    ("SEA", "Sam Darnold", "QB", "Ribs, Quadricep", DNP, "Out", 4),
    ("SEA", "Derick Hall", "LB", B, DNP, B, 4),
    ("SEA", "Drew Lock", "QB", B, LIM, B, 4),
    ("SEA", "Quenton Nelson", "G", "Knee", DNP, "Out", 4),
    ("SEA", "Uchenna Nwosu", "LB", B, FULL, B, 4),
    ("SEA", "Patrick O'Connell", "LB", B, FULL, B, 4),
    ("SEA", "Connor O'Toole", "LB", B, FULL, B, 4),
    ("SEA", "Brandon Pili", "DT", B, FULL, B, 4),
    ("SEA", "Jarran Reed", "DT", B, FULL, B, 4),
    ("SEA", "Rashid Shaheed", "WR", B, FULL, B, 4),
    ("SEA", "Jaxon Smith-Njigba", "WR", B, FULL, B, 4),
    ("SEA", "Leonard Williams", "DT", "Stinger", DNP, "Out", 4),
    ("LV", "Thomas Booker", "DT", "Ankle", FULL, "Questionable", 4),
    ("LV", "Foley Fatukasi", "DT", B, FULL, B, 4),
    ("LV", "Ian Thomas", "TE", B, FULL, B, 4),
    ("LV", "Dont'e Thornton Jr.", "WR", "Back", DNP, "Questionable", 4),
    ("LV", "Trey Zuhn III", "C", B, FULL, B, 4),
    # ---- SF @ DAL (4:25 PM) -- chunks 4/5
    ("SF", "Mike Evans", "WR", "Achilles", DNP, "Out", 4),
    ("SF", "Renardo Green", "CB", "Back", LIM, "Questionable", 4),
    ("SF", "Dre Greenlaw", "LB", "Knee", LIM, "Questionable", 4),
    ("SF", "Nate Hobbs", "CB", "Groin", FULL, "Questionable", 4),
    ("SF", "Deommodore Lenoir", "CB", "Foot", LIM, "Questionable", 4),
    ("SF", "Christian McCaffrey", "RB", B, FULL, B, 5),
    ("SF", "Siran Neal", "S", B, FULL, B, 5),
    ("SF", "Demarcus Robinson", "WR", B, FULL, B, 5),
    ("SF", "Deebo Samuel Sr.", "WR", B, FULL, B, 5),
    ("SF", "Upton Stout", "CB", "Shoulder, Neck", LIM, "Questionable", 5),
    ("SF", "C.J. West", "DT", "Knee", FULL, "Questionable", 5),
    ("SF", "Trent Williams", "T", "Shoulder", DNP, "Questionable", 5),
    ("DAL", "DaRon Bland", "CB", "Ankle", LIM, "Questionable", 5),
    ("DAL", "Jonathan Bullard", "DT", "Calf", FULL, "Questionable", 5),
    ("DAL", "Alijah Clark", "S", "Illness", DNP, "Questionable", 5),
    ("DAL", "Donovan Ezeiruaku", "LB", "Ankle", DNP, "Out", 5),
    ("DAL", "Jake Ferguson", "TE", "Knee, Ankle", DNP, "Out", 5),
    ("DAL", "Tyler Goodson", "RB", "Ankle, Knee", DNP, "Out", 5),
    ("DAL", "Malik Hooker", "S", B, DNP, B, 5),
    ("DAL", "Marist Liufau", "LB", B, FULL, B, 5),
    ("DAL", "P.J. Locke", "S", "Concussion", DNP, "Out", 5),
    ("DAL", "Von Miller", "LB", B, DNP, B, 5),
    ("DAL", "Jonathan Mingo", "WR", "Ankle", DNP, "Out", 5),
    ("DAL", "Devin Moore", "CB", "Hip", FULL, "Questionable", 5),
    ("DAL", "DeMarvion Overshown", "LB", B, FULL, B, 5),
    ("DAL", "George Pickens", "WR", B, FULL, B, 5),
    ("DAL", "Joey Porter Jr.", "CB", "Ankle, Foot", LIM, "Questionable", 5),
    ("DAL", "Luke Schoonmaker", "TE", B, FULL, B, 5),
    ("DAL", "Brevyn Spann-Ford", "TE", B, FULL, B, 5),
    ("DAL", "Juanyeh Thomas", "S", "Hamstring", DNP, "Doubtful", 5),
    ("DAL", "KaVontae Turpin", "WR", B, FULL, B, 5),
    # ---- PIT @ CIN (8:20 PM) -- chunk 5
    ("PIT", "Brandin Echols", "CB", B, FULL, B, 5),
    ("PIT", "DeShon Elliott", "S", B, FULL, B, 5),
    ("PIT", "Derrick Harmon", "DT", "Foot", FULL, "Questionable", 5),
    ("PIT", "Cameron Heyward", "DT", B, FULL, B, 5),
    ("PIT", "Ben Skowronek", "WR", B, FULL, B, 5),
    ("PIT", "Doneiko Slaughter", "CB", B, FULL, B, 5),
    ("PIT", "Darnell Washington", "TE", B, FULL, B, 5),
    ("PIT", "T.J. Watt", "LB", B, FULL, B, 5),
    ("CIN", "Jonathan Allen", "DT", B, LIM, B, 5),
    ("CIN", "Jalen Davis", "CB", "Hamstring", FULL, "Doubtful", 5),
    ("CIN", "Kyle Dugger", "S", "Quadricep", DNP, "Out", 5),
    ("CIN", "Dylan Fairchild", "G", B, FULL, B, 5),
    ("CIN", "B.J. Hill", "DT", B, DNP, B, 5),
    ("CIN", "Andrei Iosivas", "WR", "Thumb", FULL, "Doubtful", 5),
    ("CIN", "Dexter Lawrence", "DT", B, DNP, B, 5),
    ("CIN", "Brian Parker II", "G", "Knee", FULL, "Doubtful", 5),
    ("CIN", "DJ Turner II", "CB", B, FULL, B, 5),
    # ---- LAC @ BAL (Monday, November 16) -- chunks 5/6
    ("LAC", "Kayode Awosika", "G", "Fibula", FULL, "Questionable", 5),
    ("LAC", "Bud Dupree", "DE", B, FULL, B, 5),
    ("LAC", "Justin Eboigbe", "DE", "Ankle", LIM, "Questionable", 5),
    ("LAC", "Alex Harkey", "G", B, FULL, B, 5),
    ("LAC", "Tre Harris", "WR", B, FULL, B, 5),
    ("LAC", "Cam Hart", "CB", B, FULL, B, 5),
    ("LAC", "Daiyan Henley", "LB", B, FULL, B, 5),
    ("LAC", "Deane Leonard", "CB", B, FULL, B, 5),
    ("LAC", "Khalil Mack", "LB", B, FULL, B, 5),
    ("LAC", "Ladd McConkey", "WR", "Back", DNP, "Questionable", 5),
    ("LAC", "Keaton Mitchell", "RB", B, FULL, B, 5),
    ("LAC", "David Njoku", "TE", "Fibula", FULL, "Questionable", 5),
    ("LAC", "Denzel Perryman", "LB", "Pectoral", FULL, "Questionable", 5),
    ("LAC", "Trey Pipkins", "T", "Not injury related - personal matter, Knee", LIM, "Questionable", 5),
    ("LAC", "Rodney Shelley", "CB", B, FULL, B, 5),
    ("LAC", "Branson Taylor", "G", "Ankle", DNP, "Out", 5),
    ("LAC", "Brenen Thompson", "WR", "Hamstring", DNP, "Doubtful", 6),
    ("LAC", "Isas Waxter", "CB", "Ankle", DNP, "Out", 6),
    ("LAC", "Kendall Williamson", "S", "Calf", DNP, "Out", 6),
    ("BAL", "Rasheen Ali", "RB", B, FULL, B, 6),
    ("BAL", "Rashod Bateman", "WR", B, FULL, B, 6),
    ("BAL", "Calais Campbell", "DT", B, DNP, B, 6),
    ("BAL", "Kyle Hamilton", "S", B, FULL, B, 6),
    ("BAL", "Jaylinn Hawkins", "S", "Knee", LIM, "Out", 6),
    ("BAL", "Matthew Hibner", "TE", B, FULL, B, 6),
    ("BAL", "Olaivavega Ioane", "G", B, FULL, B, 6),
    ("BAL", "Adam Randall", "RB", "Neck, Hamstring", FULL, "Questionable", 6),
    ("BAL", "Ronnie Stanley", "T", B, DNP, B, 6),
    ("BAL", "Nate Wiggins", "CB", B, FULL, B, 6),
]

CLUB_NAME = {
    "WAS": "Washington Commanders", "NYG": "New York Giants",
    "NE": "New England Patriots", "DET": "Detroit Lions",
    "KC": "Kansas City Chiefs", "ATL": "Atlanta Falcons",
    "MIN": "Minnesota Vikings", "GB": "Green Bay Packers",
    "JAX": "Jacksonville Jaguars", "TEN": "Tennessee Titans",
    "BUF": "Buffalo Bills", "NYJ": "New York Jets",
    "MIA": "Miami Dolphins", "IND": "Indianapolis Colts",
    "CAR": "Carolina Panthers", "NO": "New Orleans Saints",
    "HOU": "Houston Texans", "CLE": "Cleveland Browns",
    "LAR": "Los Angeles Rams", "AZ": "Arizona Cardinals",
    "SEA": "Seattle Seahawks", "LV": "Las Vegas Raiders",
    "SF": "San Francisco 49ers", "DAL": "Dallas Cowboys",
    "PIT": "Pittsburgh Steelers", "CIN": "Cincinnati Bengals",
    "LAC": "Los Angeles Chargers", "BAL": "Baltimore Ravens",
}

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    out = os.path.join(HERE, "data", "injuries_wk10.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fields = ["row_id", "week", "club", "club_name", "player", "position",
              "injury_description", "practice_status", "game_status",
              "designation_present", "source_url", "fetched_utc", "page_chunk"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for i, (club, player, pos, inj, prac, game, chunk) in enumerate(ROWS, start=1):
            w.writerow({
                "row_id": "INJ-10-%03d" % i,
                "week": WEEK,
                "club": club,
                "club_name": CLUB_NAME[club],
                "player": player,
                "position": pos,
                "injury_description": inj,
                "practice_status": prac,
                "game_status": game,
                "designation_present": "no" if game == B else "yes",
                "source_url": SRC,
                "fetched_utc": FETCHED,
                "page_chunk": chunk,
            })

    # Per-club summary (counts only; no interpretation)
    order = []
    agg = {}
    for club, _p, _po, _i, prac, game, _c in ROWS:
        if club not in agg:
            agg[club] = {"rows": 0, "dnp": 0, "limited": 0, "full": 0,
                         "out": 0, "doubtful": 0, "questionable": 0, "blank_status": 0,
                         "blank_injury_desc": 0}
            order.append(club)
        a = agg[club]
        a["rows"] += 1
        a["dnp"] += prac == DNP
        a["limited"] += prac == LIM
        a["full"] += prac == FULL
        a["out"] += game == "Out"
        a["doubtful"] += game == "Doubtful"
        a["questionable"] += game == "Questionable"
        a["blank_status"] += game == B
        a["blank_injury_desc"] += _i == B
    sout = os.path.join(HERE, "data", "injuries_wk10_summary.csv")
    with open(sout, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["club", "club_name", "player_rows", "practice_DNP", "practice_LP",
                    "practice_FP", "game_Out", "game_Doubtful", "game_Questionable",
                    "game_status_blank", "injury_description_blank", "source_url"])
        for club in order:
            a = agg[club]
            w.writerow([club, CLUB_NAME[club], a["rows"], a["dnp"], a["limited"], a["full"],
                        a["out"], a["doubtful"], a["questionable"], a["blank_status"],
                        a["blank_injury_desc"], SRC])
    print("injuries_wk10.csv rows:", len(ROWS), "clubs:", len(order))
    tot = {
        "Out": sum(1 for r in ROWS if r[5] == "Out"),
        "Doubtful": sum(1 for r in ROWS if r[5] == "Doubtful"),
        "Questionable": sum(1 for r in ROWS if r[5] == "Questionable"),
        "BLANK": sum(1 for r in ROWS if r[5] == B),
    }
    print("game status totals:", tot)


if __name__ == "__main__":
    main()
