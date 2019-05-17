#!/usr/bin/python

import sys
import csv
import re
import copy

class CourseSect(object):
  def __init__(self): 
    self.subject = ""
    self.coursenum = 0
    self.courseid = 0
    self.section = 0 
    self.dates = []
    self.days = []
    self.times = []
    self.status = ""
    self.instructors = []
    self.delmeth = ""

  def display(self):
    print("{} {}-{} ID: {}".format(self.subject, self.coursenum, self.section, self.courseid))

class Course(object):
  def __init__(self):
    self.subject = ""
    self.coursenum = 0
    self.title = ""
    self.crhr = 0
    self.allsect = []
  
  def display(self):
    print("{} {}: {}".format(self.subject,self.coursenum,self.title))

def SortCourses(ListOfCourses): 

    # Use the Bubble Sort method to rearrange the list of courses. 
    # Courses with fewer sections will be listed first.

    n = len(ListOfCourses) 
    for i in range(n):   # i labels a Course Object within the list
        for j in range(0, n-i-1):  # j labels another Course Object within the list
            lenc1 = len(ListOfCourses[j].allsect)
            lenc2 = len(ListOfCourses[j+1].allsect)
            if lenc1 > lenc2 : 
                ListOfCourses[j], ListOfCourses[j+1] = ListOfCourses[j+1], ListOfCourses[j]
 
def make_dt_dict(sect):

   # This function returns a dictionary that links a day (M, T, W, Th, or F) to a
   # list of time ranges (e.g. 11:00am-11:50am, 11:00am-12:20pm, etc.). The time
   # ranges are stored as strings. 
   # 
   # Input "sect" must be a CourseSect object.

   dt_dict = {}
   daylist = []
   timelist = []

   # Determine whether or not the last day and time listed for a CourseSect
   #  object is a Final Exam day. If it is a final exam day, then do not
   #  include it in the final dictionary that links days to time ranges.

   lastinst = sect.instructors[len(sect.instructors)-1]
   p = re.compile("FINAL EXAM")

   if p.search(lastinst):
      lastday = len(sect.days)-1
   else: 
      lastday = len(sect.days)

   for i in range(0,lastday):
      tdlist = sect.days[i].split(' ')
      for j in range(0,len(tdlist)):
          daylist.append(tdlist[j])
          timelist.append(sect.times[i])

   sort_dt(daylist, timelist)

   i = 0
   while (i < len(daylist)):
     ttlist = []
     ttlist.append(timelist[i])
     j = i
     i = i + 1
     while i < len(daylist) and daylist[i] == daylist[i-1]:
       ttlist.append(timelist[i])
       i = i + 1
     dt_dict[daylist[j]] = ttlist

   return dt_dict
       
def sort_dt(daylist, timelist):

    # Use the Bubble Sort method to sort a list of days (M, T, W, Th, F) in
    #  order by the "ordinal" of the day (the number assigned to the character
    #  in python). Simultaneously sort timelist. The two lists should be
    #  the same length.

    n = len(daylist)
    for i in range(n):   
        for j in range(0, n-i-1):
            if daylist[j] == "Th":
                daylj = ord("R")
            else:
                daylj = ord(daylist[j]) 
            if daylist[j+1] == "Th":
                dayljp1 = ord("R")
            else:
                dayljp1 = ord(daylist[j+1])
            
            if daylj > dayljp1:
                daylist[j], daylist[j+1] = daylist[j+1], daylist[j]
                timelist[j], timelist[j+1] = timelist[j+1], timelist[j]

def time_to_min(timestring):

  # This function converts a string in the form "1:50pm" to minutes of the day.
  #  For example, "1:50pm" corresponds to minute number 830 of the day (out of 
  #  1440 possible minutes in each 24-hr day).

  am = re.compile("am")
  pm = re.compile("pm")

  tlist = timestring.split(":")
  hour = int(tlist[0])
  min = int(tlist[1][0:2])

  if am.search(timestring):
    addfactor = 0
  elif pm.search(timestring):
    if hour == 12:
      hour = 0
    addfactor = 720
  else:
    print("Cannot deterimine if this time is am or pm in function time_to_min")

  nminute = 60*hour + min + addfactor

  return nminute
     
def split_time(mtimerange):

  # This function takes a "messy" string time range (mtimerange) and splits it
  #  into a start time (integer, in minutes) and end time (integer, in minutes)
  #  It returns a 2-member integer list where the first number is the
  #  start time and the second number is the end time.

  tlist = []

  mtimerange = mtimerange.decode('utf-8')

  stimelist = mtimerange.split(u'\xa0-\xa0')
# print("in split_time stimelist = ",stimelist)    # DEBUG
  tlist.append(time_to_min(stimelist[0]))
  tlist.append(time_to_min(stimelist[1]))

  return tlist


def compare_sect(secta,sectb):

   # The arguments secta and sectb must be CourseSect objects. This 
   # function compares the dates and times of the two sections. 
   # Return value will be "0" if there is no day&time conflict.
   # Return value will be "1" if there is a day&time conflict.

    dt_dict_a = make_dt_dict(secta)
    dt_dict_b = make_dt_dict(sectb)
 
    conflict = 0

    for day_a in dt_dict_a.keys():
      if day_a in dt_dict_b:
        timelist_a = dt_dict_a[day_a]
        timelist_b = dt_dict_b[day_a]
        conflict = compare_times(timelist_a, timelist_b)
        if conflict == 1:
           break
    
#   print("in compare_sect outside loop",conflict)   # DEBUG

#   if conflict == 1:						# DEBUG
#      print("Conflict found",secta.courseid,sectb.courseid)    # DEBUG

    return conflict

def compare_times(stimesa, stimesb):

   # The arguments timesa and timesb must be string lists of time 
   #  ranges. Returns conflict = 0 if there is no overlap between
   #  time ranges. Returns conflict = 1 if there is an overlap
   #  time ranges.

    i = 0

    conflict = 0

    while (i < len(stimesa)) and (conflict == 0):
       j = 0
       while (j < len(stimesb)) and (conflict == 0):
          timerange_a = split_time(stimesa[i])
          timerange_b = split_time(stimesb[j])
#         print("In compare_times",timerange_a,timerange_b)    # DEBUG
          if timerange_a[0] < timerange_b[0]:
              if timerange_b[0] < timerange_a[1]:
            # if timerange_b[0] < timerange_a[1] or timerange_b[1] <= timerange_a[1]:
                  conflict = 1
          else:
              if timerange_a[0] < timerange_b[1]:
            # if timerange_a[0] < timerange_b[1] or timerange_a[1] <= timerange_b[1]:
                  conflict = 1
          j += 1
       i += 1

#   print("in compare_times conflict = ",conflict)   # DEBUG
    return conflict

def check_schedule(sched,sect):
 
   # "sched" = a list of CourseSect objects. 
   # "sect" = a specific CourseSect object.
   # 
   # This function checks to see if course section "sect" conflicts with
   # any of the sections in the given schedule.
   # 
   # This function returns conflict = 0 if there are no conflicts between any 
   # sections in the given schedule.

   conflict = 0
   i = 0

   while i < (len(sched)) and conflict == 0:
      conflict = compare_sect(sched[i],sect)
      i += 1

   return conflict

# ------------------ START MAIN PROGRAM ----------------------------- # 
# Read in the .csv file containing course information
# Note: this script assumes that the .csv file has a header row, and 
#       ultimately deletes the information stored in the header row.

try:
  filepath="/Users/Hannah/Documents/Home/PythonPractice/CourseScheduler/"
  filetot = filepath + str(sys.argv[1])
except:
  print("Please enter the name of the .csv file containing course information.")
  sys.exit()

print(filetot)

  # Initialize variables that will be read from the .csv file and 
  #   used to define course objects.

cids = []
csubs = []
cnums = []
csects = [] 
ctitles = []
cdates = []
cdays = []
ctimes = []
ccrhr = []
cstatus = []
cinstrucs = []
cdelmeths = []

all_clists = [cids, csubs, cnums, csects, ctitles, cdates, cdays, ctimes, ccrhr, cstatus, cinstrucs, cdelmeths]

with open(filetot) as csvfile:
  course_raw_info = csv.reader(csvfile)
 
  for row in course_raw_info:
    for i in range(0,len(all_clists)):
      all_clists[i].append(row[i])

# Delete the header row from each list
for i in range(0,len(all_clists)):
  del all_clists[i][0]

#   Now go through the list of sections and add additional courses to course_list
#    as needed. Individual sections will be stored as CourseSect objects within 
#    the "allsect" list of each course object.

course_list = []
ncourse = 0 

for id in range (0,len(cids)):
  if (id == 0):
    new_course = Course()
    course_list.append(new_course)
  else: 
    if (cnums[id] != cnums[id-1]) or (csubs[id] != csubs[id-1]):
      ncourse += 1
      new_course = Course()
      course_list.append(new_course)
  course_sect = CourseSect()
  course_list[ncourse].subject = csubs[id]
  course_list[ncourse].coursenum = cnums[id]
  course_list[ncourse].title = ctitles[id]
  course_list[ncourse].crhr = ccrhr[id]
  course_list[ncourse].allsect.append(course_sect)

  course_sect.subject = csubs[id]
  course_sect.coursenum = cnums[id]
  course_sect.courseid = cids[id]
  course_sect.section = csects[id]
  course_sect.status = cstatus[id]
  course_sect.delmeth = cdelmeths[id]
  course_sect.dates = cdates[id].split('\n')
  course_sect.days = cdays[id].split('\n')
  course_sect.times = ctimes[id].split('\n')
  course_sect.instructors = cinstrucs[id].split('\n')

# Sort the courses by number of sections. 

SortCourses(course_list)

# Print sorted courses:

for nc in range(0,len(course_list)):
  print("{} Course: {} {}".format(nc,course_list[nc].subject, course_list[nc].coursenum))
  for isec in range(0,len(course_list[nc].allsect)):
    print("   {}  Course ID = {}".format(isec,course_list[nc].allsect[isec].courseid))

# For each section in the course withe the fewest sections, look at each section in 
#  the other courses and see if a plausible schedule can be built. 

#  Initialize schedule_list with the list of all sections of the course with the
#   fewest sections.

schedule_list = []    # This is a list of all plausible schedules. 
                      #  Each schedule in the list is a list of CourseSect objects.
nsched = 0

for i in range(0,len(course_list[0].allsect)):
   schedule_list.append([course_list[0].allsect[i]])
   nsched += 1

# Go through each of the remaining sections of each course and check each one for 
#  compatibility with the current list of possible schedules (schedule_list).

for i in range(1,len(course_list)):

   len_slist = len(schedule_list)

   for j in range(0, len_slist):

      for sect in course_list[i].allsect:

         conflict = 0
         
         lslistj = len(schedule_list[j])

         if lslistj == i + 1:
            tempsched = []
            for k in range(0,lslistj-1):
              tempsched.append(schedule_list[j][k])
         elif lslistj == i:
            tempsched = schedule_list[j]
         else:
            print("error: length of schedule = ",lslistj)

         conflict = check_schedule(tempsched,sect)
    
         if conflict == 0:
            if lslistj == i + 1:
               newsched = copy.deepcopy(schedule_list[j])
               newsched.pop(lslistj-1)
               newsched.append(sect)
               schedule_list.append(newsched)
            elif lslistj == i:
               schedule_list[j].append(sect)
            else:
               print("Error in main program: length of schedule list = ",lslistj)
         else:
            print("Found conflict (main program)!")

i = 0
for sched in schedule_list:

   i += 1
   print("NEW SCHEDULE:",i)

   for sect in sched:
      sect.display()
      sdt_dict = make_dt_dict(sect)
      for day in sdt_dict:
         print("  {}".format(day))

