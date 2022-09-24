import pandas as pd
import numpy as np
import sys
import os

class roomfinder:
    def __init__(self, filepath):
        # Read excel into pandas DF
        try:
            self.df = pd.read_excel(filepath)
        except FileNotFoundError:
            print(f'{bcolors.FAIL}ERROR:{bcolors.ENDC} Failed to read excel data.')
            sys.exit(1)

        # Reformat df for room findability
        self.reformat()
        
        # Keep a list of classrooms
        self.room_list = np.array(sorted(np.unique(self.df['Bldg/Rm'])))            

    def reformat(self):
        # Set index to CRN, drop rows that don't have a CRN (aka exams, non-classes) or are remote only
        self.df = self.df.set_index('CRN')
        self.df = self.df.dropna()
        self.df = self.df.drop(self.df[self.df['Bldg/Rm'] == 'REMOTE ONLY'].index,axis = 0)

        # Drop lab classrooms, as those aren't open to students unless class in session
        self.df = self.df[self.df['Actv'] != 'LAB']

        # Drop irrelevant columns
        self.df = self.df.drop(['Course #','Course Title','Units','Actv','Start - End','Instructor','Max Enrl', 'Act Enrl','Seats Avail'],axis = 1)
        
        # Twelve hour constant for readability
        twelve_hours = pd.Timedelta(12, unit='h')
        # Split time column into a start and an end column.
        temp = self.df['Time'].str.split(pat='-',expand=True)
        self.df = self.df.drop('Time', axis = 1)
        # Add column to track if am or pm. If pm, 12 hours. If am, 0 hours
        self.df['meridiem'] = temp[1].str[-2:]
        self.df['meridiem'] = twelve_hours * (self.df['meridiem'] == 'pm').astype(int)

        # Change to military time
        # Format start and end as timedelta objects to measure difference
        self.df['Start'] = pd.to_timedelta(pd.to_datetime(temp[0],format= '%H:%M').dt.hour, unit = 'h') + pd.to_timedelta(pd.to_datetime(temp[0],format= '%H:%M').dt.minute, unit = 'm')
        self.df['End'] = pd.to_timedelta(pd.to_datetime(temp[1].str[:-2],format= '%H:%M').dt.hour, unit = 'h') + pd.to_timedelta(pd.to_datetime(temp[1].str[:-2],format= '%H:%M').dt.minute,unit='m')
        # Add meridiem (0/12 hours for am/pm) to End, making sure to % to account for 12 pm
        self.df['End'] = self.df['End'] % twelve_hours + self.df['meridiem']
        # If the difference between End and Start is more than twelve hours, Start must also be in pm. Add twelve hours.
        self.df['period'] = self.df['End'] - self.df['Start']
        self.df['period'] = self.df['period'] > twelve_hours
        self.df['Start'] = self.df['Start'] + twelve_hours * self.df['period'].astype(int)
        # Drop temp columns
        self.df = self.df.drop(['meridiem','period'],axis=1)

        return self.df
        
    def find_room(self, day, start_str, end_str):
        try:
            # Parse time inputs
            temp = list(map(int, start_str.split(':')))
            start = pd.to_timedelta(temp[0], unit = 'h') + pd.to_timedelta(temp[1],unit = 'm')
            temp = list(map(int, end_str.split(':')))
            end = pd.to_timedelta(temp[0], unit = 'h') + pd.to_timedelta(temp[1],unit = 'm')

            # Check for valid input
            assert day in ['M','T','W','R','F']
            assert end > start

        except AssertionError as a:
            print(f'{bcolors.FAIL}ERROR:{bcolors.ENDC} Invalid inputs.')
            sys.exit(1)

        except Exception as e:
            print(f'{bcolors.FAIL}ERROR:{bcolors.ENDC} Cannot parse time inputs. Please format your input as HH:MM, in military time.')
            sys.exit(1)

        else:
            # Find all classes that occur at any point in the time frame.
            occupied = self.df[self.df['Days'].str.contains(day)].copy()
            occupied = occupied[((occupied['Start'] > start) & (occupied['Start'] < end)) | ((occupied['End'] > start) & (occupied['End'] < end)) | ((occupied['Start'] < start) & (occupied['End'] > end))]
            # Set occupied to array of room names
            occupied = np.array(sorted(pd.unique(occupied['Bldg/Rm'])))

            # Set available to list of rooms not in occupied
            idx_del = []
            for i in occupied:
                idx_del.append(int(np.where(self.room_list == i)[0]))
            available = np.delete(self.room_list, idx_del)

            # Return both lists
            return available, occupied

# ooh wow pretty colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

if __name__ == "__main__":
    # make pretty colors active if on windows
    try:
        os.system('color')
    except:
        pass

    filepath = input("Please input filepath of excel data.\n:")
    day = input("What day are you looking at (M/T/W/R/F)?\n:")
    start = input("From what time (military, HH:MM)?\n:")
    end = input("Until what time (military, HH:MM)?\n:")

    finder = roomfinder(filepath)
    available, occupied = finder.find_room(day,start,end)

    print(f"{bcolors.OKGREEN}Available rooms:{bcolors.ENDC}")
    print(available)
    print(f"{bcolors.WARNING}Occupied:{bcolors.ENDC}")
    print(occupied)