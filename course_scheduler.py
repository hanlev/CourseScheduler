#!/usr/bin/python

import sys
import csv
import re
import os
import copy
import requests
from bs4 import BeautifulSoup


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

def get_course_sections(response):

    # Returns a list of CourseSection objects from the html of
    #  a WSU eServices search result for a given course.

    new_sect_list = []

    soup = BeautifulSoup(response.content, 'html.parser')

    course_html_table = soup.find(id="resultsTable")
    course_tbody = course_html_table.find('tbody')
    course_rows = course_tbody.find_all('tr')

    for row in course_rows:
        cell = row.find_all('td')
        course_sect = CourseSect()
        course_sect.subject = cell[2].get_text().strip()
        course_sect.coursenum = cell[3].get_text().strip()
        course_sect.courseid = cell[1].get_text().strip()
        course_sect.section = cell[4].get_text().strip()
        course_sect.status = cell[9].get_text()
        course_sect.delmeth = cell[12].get_text()
        course_sect.dates = cell[6].get_text()

        for div in cell[7].find_all('div'):
            course_sect.days.append(div.get_text().strip())

        for div in cell[8].find_all('div'):
            course_sect.times.append(div.get_text().strip())

        for div in cell[11].find_all('div'):
            course_sect.instructors.append(div.get_text().strip())

        course_sect.dtdict = make_dt_dict(course_sect)

#       course_sect.display()    # DEBUG

        new_sect_list.append(course_sect)

    return new_sect_list


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
      tdlist = sect.days[i].split('\n')
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
     
def clean_time_range(mtimerange):

  # This function takes a "messy" string time range (mtimerange) that
  # involves Latin-1 (ISO/IEC 8859-1:1998) symbols (e.g. \xa0 or \xc2\xa0
  # for a non-breaking space) and converts it to a "clean" string in the 
  # form "11:30am-12:20pm"

  tstring = ""
  tlist = []

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

   # The arguments stimesa and stimesb must be string lists of time 
   #  ranges (e.g. ["10:00am-10:50am","3:00pm-4:20pm"]). 
   #  Returns conflict = 0 if there is no overlap between
   #  time ranges. Returns conflict = 1 if there is an overlap
   #  time ranges.

    i = 0

    conflict = 0

    while (i < len(stimesa)) and (conflict == 0):
       j = 0
       while (j < len(stimesb)) and (conflict == 0):
          timerange_a = stimesa[i].split("-")
          timerange_b = stimesb[j].split("-")
          time_a0 = time_to_min(timerange_a[0])
          time_a1 = time_to_min(timerange_a[1])
          time_b0 = time_to_min(timerange_b[0])
          time_b1 = time_to_min(timerange_b[1])
#         print("In compare_times",timerange_a,timerange_b)    # DEBUG
          if time_a0 < time_b0:
              if time_b0 < time_a1:
                  conflict = 1
          else:
              if time_a0 < time_b1:
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

def min_to_time(minute):

   # This function takes a time in minutes (e.g. 740) and converts it into a human-readable time,
   #   the string "12:20pm".

   if (minute >= 0) and (minute < 60):
     hour = int(12)
     ampm = "am"
   elif (minute >= 60) and (minute <720):
     hour = int(minute/60)
     ampm = "am"
   elif (minute >= 720) and (minute < 780):
     hour = int(minute/60)
     ampm = "pm"
   elif (minute >= 780) and (minute < 1440):
     minute = minute - 720
     hour = int(minute/60)
     ampm = "pm"
   else:
      print("{} is an invalid number of minutes in the day".format(minute))

   min = str(minute % 60)

   if ((minute % 60) < 10):
      min = "0" + min
      
   time = str(hour) + ":" + min + ampm
   return(time)


def make_html_weekday_header(i):

   xwidth_tot = 8*day_xpx
   yheight_tot = orig_ypx + 15*hour_ypx     # The schedule ranges a total of 15 hours, from 7am to 10pm
   daylist = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

   print("<h3>Schedule #{}</h3>".format(i))
   print("")

   print("<svg width=\"{}\" height=\"{}\">".format(xwidth_tot,yheight_tot))

   for i in range(0,len(daylist)):
      day_xloc = (i+1)*day_xpx
      print('''  <rect x="{}" y="0" rx="{}" ry="{}" width="{}" height="{}" style="fill: blue; stroke: black; stroke-width: 1; opacity: 0.3;"></rect> '''.format(day_xloc,rpx,rpx,day_xpx,orig_ypx))
      print('''  <text x="{}" y="{}" fill="black">{}</text> '''.format(text_indent+day_xloc,text_down,daylist[i]))

   for imin in range(sched_start_min,sched_end_min,60):
      st_time = min_to_time(imin)
      yrect = (imin - sched_start_min) * hour_ypx/60 + orig_ypx
#     print(imin,st_time,yrect) 			# DEBUG
      print('''  <rect x="0" y="{}" rx="{}" ry="{}" width="{}" height="{}" style="fill: blue; stroke: black; stroke-width: 1; opacity: 0.3;"></rect> '''.format(yrect,rpx,rpx,day_xpx,hour_ypx))
      print('''  <text x="{}" y="{}" fill="black">{}</text> '''.format(text_indent,yrect+text_down,st_time))


def pr_html_sect(sect,color,opac):

  # This function prints out html svg code for depictions of where
  #  a given section appears within a schedule.

   rect_xval = {"M":(day_xpx*2), "T":(day_xpx*3), "W":(day_xpx*4), "Th":(day_xpx*5), "F":(day_xpx*6)}

   for day in sect.dtdict:

      rect_x = rect_xval[day]
#     print(day,rect_x)			# DEBUG PR
 
      for timerange in sect.dtdict[day]:

#        print(timerange)              # DEBUG PR
 
         stlist = timerange.split('-')
         time0 = time_to_min(stlist[0])
         time1 = time_to_min(stlist[1])
         rect_yi = (time0 - sched_start_min) * hour_ypx / 60 + orig_ypx  
         yh = (time1 - time0) * hour_ypx / 60
         txt_x = rect_x + text_indent
         txt_y = rect_yi + text_down

#        print("time0 = {} time1 = {} yh = {} hour_ypx = {}".format(time0,time1,yh,hour_ypx))  # DEBUG PR
         
         print('''
   <rect x="{}" y="{}" rx="{}" ry="{}" width="{}" height="{}" style="fill: {}; stroke: black; stroke-width: 1; opacity: {};"></rect>
'''.format(rect_x,rect_yi,rpx,rpx,day_xpx,yh,color,opac))

         print('''
   <text x="{}" y="{}" fill="black">{} {}-{}</text>
'''.format(txt_x,txt_y,sect.subject,sect.coursenum,sect.section,txt_x,txt_y+13,stlist[0],txt_x,txt_y+26,stlist[1]))

# ------------------ START MAIN PROGRAM ----------------------------- # 

# Set the global variables that define how the HTML SVG schedule will look

orig_ypx = 30    # this is the pixel height devoted to the weekday header in html svg schedule
day_xpx  = 100   # this is the pixel width devoted to one weekday in the html svg schedule
hour_ypx = 30   # this is the pixel height devoted to 1 hour of time on schedule
rpx = 10         # this is the pixel amount by which each rectangle corner is "rounded"
text_indent = 5  # this is the pixel amount by which the text is indented inside of a section rectangle
text_down = 20   # this is the pixel amount by which the text appears below the top of a section rectangle
sched_start_min = 420    # This is the first time shown on the schedule expressed in minutes (e.g. 420 = 7:00am)
sched_end_min   = 1320   # This is the last time shown on the schedule expressed in minutes (e.g. 1320 = 10:00pm)
color_list = ["red","green","yellow","purple","orange","blue"]
opac_list = [0.3, 0.3, 0.4, 0.3, 0.4, 0.4]

# Read in the .csv file containing course information
# Note: this script assumes that the .csv file has a header row, and 
#       ultimately deletes the information stored in the header row.

try:
  filepath = os.getcwd()
  filetot = filepath + "\\" + str(sys.argv[1])
except:
  print("Please enter the name of the .csv file containing course information.")
  sys.exit()

print(filetot)

# Read a .csv file containing the list of desired courses for a
#  semester, e.g. CHEM,213 \n  BIOL,242 \n etc.

course_list = []

with open(filetot) as csvfile:
  course_raw_info = csv.reader(csvfile)
 
  for row in course_raw_info:
      new_course = Course()
      new_course.subject = row[0]
      new_course.coursenum = row[1]
      course_list.append(new_course)

# For each course listed, get information from WSU's eServices
#   site about the sections being offered

# semester = str(20213)  # this stands for Fall 2021
semester = str(20205)  # this stands for Spring 2020

url_pt01 = 'https://eservices.minnstate.edu/registration/search/advancedSubmit.html?campusid=074&searchrcid=0074&searchcampusid=074&yrtr=' + semester + '&subject='
url_pt02 = '&courseNumber='
url_pt03 = '&courseId=&openValue=ALL&delivery=ALL&showAdvanced=&starttime=&endtime=&mntransfer=&gened=&credittype=ALL&credits=&instructor=&keyword=&begindate=&site=&resultNumber=250'

for course in course_list:
    course.display()
    url_tot = url_pt01 + course.subject + url_pt02 + str(course.coursenum) + url_pt03
    html_response = requests.get(url_tot)
    if(html_response.status_code > 400):
        print("There was an error opening the website for " + course.subject + " " + str(course.coursenum))

    course.allsect = get_course_sections(html_response)

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
   
      for j in range(0,len_slist):

         conflict = 0
         tempsched = []
         
         lslistj = len(schedule_list[j]) 

#        print("Testing course i={} {}{}-{}-{} with schedule j={} which has length {}".format(i,course_list[i].subject,course_list[i].coursenum,sect.section,sect.courseid,j,lslistj)) 		# DEBUG

#        for k in range(0,lslistj):			 # DEBUG  
#           print("   {}{}-{}-{} ".format(schedule_list[j][k].subject,schedule_list[j][k].coursenum,schedule_list[j][k].section,schedule_list[j][k].courseid))							# DEBUG

         if lslistj == i + 1:	
            for k in range(0,lslistj-1):
              tempsched.append(schedule_list[j][k])
            conflict = check_schedule(tempsched,sect)
            if conflict == 0:
               tempsched.append(sect)
               schedule_list.append(tempsched)
         elif lslistj == i:
            tempsched = schedule_list[j]
            conflict = check_schedule(tempsched,sect)
            if conflict == 0:
               schedule_list[j].append(sect)
         else:	
            print("error: i = {}, j = {}, length of schedule = {}".format(i,j,lslistj))	# DEBUG

# Throw an error message if no plausible schedules are found:

if (len(schedule_list) == 0 ):
   print("No plausible set of schedules found for this set of courses.")
   sys.exit()

# Print out any plausible schedules:

i = 0
for sched in schedule_list:

   if len(sched) == len(course_list):
      i += 1
      make_html_weekday_header(i)

      j = 0
      for sect in sched:
         color = color_list[j]
         opac = opac_list[j]
         pr_html_sect(sect,color,opac)
         j += 1

      print("  Sorry, your browser does not support in-line svg")
      print("</svg>")
      print("")


