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
    self.dtdict = {}
    self.status = ""
    self.instructors = []
    self.delmeth = ""

  def display(self):
    print("{} {}-{} ID: {} {}".format(self.subject, self.coursenum, self.section, self.courseid, self.dtdict))

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
          clean_times = clean_time_range(sect.times[i])
          timelist.append(clean_times)

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

#    print("In make_dt_dict ",dt_dict)        # DEBUG

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

  # This function takes a "messy" string time range (mtimerange) in the form
  #  "11:30am-12:30pm" and splits it into a start time (integer, in minutes) 
  #   and end time (integer, in minutes). It returns a 2-member integer list 
  #   where the first number is the start time and the second number is the 
  #   end time.

  tlist = []

  stimelist = mtimerange.split('-')
# print("in split_time stimelist = ",stimelist)    # DEBUG
  tlist.append(time_to_min(stimelist[0]))
  tlist.append(time_to_min(stimelist[1]))

  return tlist

def clean_time_range(mtimerange):

  # This function takes a "messy" string time range (mtimerange) that
  # involves Latin-1 (ISO/IEC 8859-1:1998) symbols (e.g. \xa0 or \xc2\xa0
  # for a non-breaking space) and converts it to a "clean" string in the 
  # form "11:30am-12:20pm"

  tstring = ""
  tlist = []

  mtimerange = mtimerange.decode('utf-8')

  stimelist = mtimerange.split(u'\xa0-\xa0')
  tlist.append(stimelist[0])
  tlist.append(stimelist[1])
  tstring = "-".join(tlist)

  return tstring

def compare_sect(secta,sectb):

   # The arguments secta and sectb must be CourseSect objects. This 
   # function compares the dates and times of the two sections. 
   # Return value will be "0" if there is no day&time conflict.
   # Return value will be "1" if there is a day&time conflict.

    dt_dict_a = secta.dtdict
    dt_dict_b = sectb.dtdict

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
                  conflict = 1
          else:
              if timerange_a[0] < timerange_b[1]:
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

def make_html_weekday_header(i):

   print("<h3>Schedule #{}</h3>".format(i))
   print("")

   print('''
<svg width="700" height="1510"> 

   <rect x="0" y="0" rx="10" ry="10" width="100" height="30" style="fill: blue; stroke: black; stroke-width: 1; opacity: 0.2;"></rect> 
   <rect x="100" y="0" rx="10" ry="10" width="100" height="30" style="fill: blue; stroke: black; stroke-width: 1; opacity: 0.2;"></rect> 
   <rect x="200" y="0" rx="10" ry="10" width="100" height="30" style="fill: blue; stroke: black; stroke-width: 1; opacity: 0.2;"></rect> 
   <rect x="300" y="0" rx="10" ry="10" width="100" height="30" style="fill: blue; stroke: black; stroke-width: 1; opacity: 0.2;"></rect> 
   <rect x="400" y="0" rx="10" ry="10" width="100" height="30" style="fill: blue; stroke: black; stroke-width: 1; opacity: 0.2;"></rect> 
   <rect x="500" y="0" rx="10" ry="10" width="100" height="30" style="fill: blue; stroke: black; stroke-width: 1; opacity: 0.2;"></rect> 
   <rect x="600" y="0" rx="10" ry="10" width="100" height="30" style="fill: blue; stroke: black; stroke-width: 1; opacity: 0.2;"></rect> 

   <text x="25" y="20" fill="black">Sunday</text> 
   <text x="120" y="20" fill="black">Monday</text> 
   <text x="220" y="20" fill="black">Tuesday</text> 
   <text x="310" y="20" fill="black">Wednesday</text> 
   <text x="420" y="20" fill="black">Thursday</text> 
   <text x="525" y="20" fill="black">Friday</text> 
   <text x="620" y="20" fill="black">Saturday</text> 

   ''')

def pr_html_sect(sect):

  # This function prints out html svg code for depictions of where
  #  a given section appears within a schedule.

   orig_ypx = 30    # this is the pixel height devoted to the weekday header in html svg schedule
   day_xpx  = 100   # this is the pixel width devoted to one weekday in the html svg schedule
   hour_ypx = 100   # this is the pixel height devoted to 1 hour of time on schedule
   rpx = 10         # this is the pixel amount by which each rectangle corner is "rounded"
   text_indent = 5  # this is the pixel amount by which the text is indented inside of a section rectangle
   text_down = 10   # this is the pixel amount by which the text appears below the top of a section rectangle

   rect_xval = {"M":day_xpx, "T":(day_xpx*2), "W":(day_xpx*3), "Th":(day_xpx*4), "F":(day_xpx*5)}

   for day in sect.dtdict:

      rect_x = rect_xval[day]
#     print(day,rect_x)			# DEBUG PR
 
      for timerange in sect.dtdict[day]:

#        print(timerange)              # DEBUG PR
 
         tlist = split_time(timerange)
         rect_yi = (tlist[0]-420)*(hour_ypx/60) + orig_ypx     # 420 min = 7:00am -- we start the schedule at 7:00am
         yh = (tlist[1] - tlist[0])*(hour_ypx/60)
         txt_x = rect_x + text_indent
         txt_y = rect_yi + text_down

#        print("yh = {}".format(yh))  # DEBUG PR
         
         print('''
   <rect x="{}" y="{}" rx="{}" ry="{}" width="{}" height="{}" style="fill: blue; stroke: black; stroke-width: 1; opacity: 0.2;"></rect>
'''.format(rect_x,rect_yi,rpx,rpx,day_xpx,yh))

         print('''
   <text x="{}" y="{}" fill="black">{} {}-{}</text>
   <text x="{}" y="{}" fill="black">{}</text>
'''.format(txt_x,txt_y,sect.subject,sect.coursenum,sect.section,txt_x,txt_y+30,timerange))

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

# Initialize the sect_mask list and a list of all course sections
#  (in the order that they appear in the original .csv file.)
#  The sect_mask list stores a "1" if the given section has been 
#  identified as an existing course or a new course

sect_mask = []
sect_list = []

for id in range (0,len(cids)):

  sect_mask.append(0)

  course_sect = CourseSect()
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
  course_sect.dtdict = make_dt_dict(course_sect)

  sect_list.append(course_sect)

# Now go through the list of sections and add additional courses to course_list
#  as needed. Individual sections will be stored as CourseSect objects within 
#  the "allsect" list of each course object.

course_list = []

for id in range (0,len(cids)):

  if (sect_mask[id] == 0):
    new_course = Course()
    new_course.subject = csubs[id]
    new_course.coursenum = cnums[id]
    new_course.title = ctitles[id]
    new_course.crhr = ccrhr[id]
    new_course.allsect.append(sect_list[id])
    course_list.append(new_course)
    sect_mask[id] = 1

    for j in range(0,len(cids)):

      if (j != id) and (sect_mask[j] == 0):
        if (csubs[id] == csubs[j]) and (cnums[id] == cnums[j]):
          new_course.allsect.append(sect_list[j])
          sect_mask[j] = 1

  
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

   for sect in course_list[i].allsect:
   
      badsched = []				# BADSCHED

      for j in range(0,len_slist):

         conflict = 0
         tempsched = []
         
         lslistj = len(schedule_list[j])

#        print("Testing course i={} {}{}-{} with schedule j={} which has length {}".format(i,course_list[i].subject,course_list[i].coursenum,sect.courseid,j,lslistj)) 		# DEBUG

#        for k in range(0,lslistj):			 # DEBUG
#           print("   {}{}-{} ".format(schedule_list[j][k].subject,schedule_list[j][k].coursenum,schedule_list[j][k].courseid))							# DEBUG

         if lslistj == i + 1:
            for k in range(0,lslistj-1):
              tempsched.append(schedule_list[j][k])
            conflict = check_schedule(tempsched,sect)
         elif lslistj == i:
            tempsched = schedule_list[j]
            conflict = check_schedule(tempsched,sect)
         else:	
#           print("error: i = {}, j = {}, length of schedule = {}".format(i,j,lslistj))	# DEBUG
            badsched.append(j)					# BADSCHED
            conflict = 1

         if conflict == 0:
            if lslistj == i + 1:
               newsched = copy.deepcopy(schedule_list[j])
               newsched.pop(lslistj-1)
               newsched.append(sect)
               schedule_list.append(newsched)
            elif lslistj == i:
               schedule_list[j].append(sect)

   for b in badsched:				# BADSCHED
      del schedule_list[b]			# BADSCHED
#     print("Deleted bad schedule",b)		# BADSCHED  # DEBUG

# Throw an error message if no plausible schedules are found:

if (len(schedule_list) == 0 ):
   print("No plausible set of schedules found for this set of courses.")
   sys.exit()

# Print out any plausible schedules:

#xxx Print html header <!DOCUMENT> etc.

i = 0
for sched in schedule_list:

   i += 1
#  print("NEW SCHEDULE: {}".format(i))
   make_html_weekday_header(i)

   for sect in sched:
#     sect.display()
      pr_html_sect(sect)

   print("  Sorry, your browser does not support in-line svg")
   print("</svg>")
   print("")


