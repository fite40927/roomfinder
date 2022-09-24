import pandas as pd
import numpy as np
import sys

class roomfinder:
    def __init__(self, filepath):
        # Read excel into pandas DF
        try:
            self.df = pd.read_excel(filepath)
        except FileNotFoundError:
            print('ERROR: Failed to read excel data.')
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
        
        # Split time column into a start and an end column.
        temp = self.df['Time'].str.split(pat='-',expand=True)
        self.df = self.df.drop('Time', axis = 1)

        # Change to military time
        # Twelve hour constant for readability
        twelve_hours = pd.Timedelta(12, unit='h')
        # Format start and end as timedelta objects to measure difference
        self.df['Start'] = pd.to_timedelta(pd.to_datetime(temp[0],format= '%H:%M').dt.hour, unit = 'h') + pd.to_timedelta(pd.to_datetime(temp[0],format= '%H:%M').dt.minute, unit = 'm')
        self.df['End'] = pd.to_timedelta(pd.to_datetime(temp[1].str[:-2],format= '%H:%M').dt.hour, unit = 'h') + pd.to_timedelta(pd.to_datetime(temp[1].str[:-2],format= '%H:%M').dt.minute,unit='m')
        # Add column to track if am or pm. If pm, 12 hours. If am, 0 hours
        self.df['meridiem'] = temp[1].str[-2:]
        self.df['meridiem'] = twelve_hours * (self.df['meridiem'] == 'pm').astype(int)
        # Add meridiem to End, making sure to % to account for 12 pm
        self.df['End'] = self.df['End'] % twelve_hours + self.df['meridiem']
        # If the difference between End and Start is more than twelve hours, also add twelve hours to Start
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
            print('ERRPR: Invalid inputs.')

        except Exception as e:
            print('ERROR: Cannot parse time inputs. Please format your input as HH:MM, in military time.')

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

if __name__ == "__main__":
    day = input("What day are you looking at (M/T/W/R/F)?\n:")
    start = input("From what time (military, HH:MM)?\n:")
    end = input("Until what time (military, HH:MM)?\n:")

    finder = roomfinder('.\class_schedule.xlsx')
    available, occupied = finder.find_room(day,start,end)

    print("Available rooms: ")
    print(available)
    print("Occupied:")
    print(occupied)