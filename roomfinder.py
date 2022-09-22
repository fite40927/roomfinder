import pandas as pd
import numpy as np

class roomfinder:
    def __init__(self, file):
        try:
            self.df = pd.read_excel(file)
            self.df = self.df.set_index('CRN')
            self.df = self.df.dropna()
            self.df = self.df.drop(self.df[self.df['Bldg/Rm'] == 'REMOTE ONLY'].index,axis = 0)
            
            self.reformat()
            
            self.room_list = np.array(sorted(np.unique(self.df['Bldg/Rm'])))
            
            self.available = 0
            self.occupied = 0
        except Exception as E:
            print(E)
    def reformat(self):
        self.df = self.df[self.df['Actv'] != 'LAB']
        self.df = self.df.drop(['Course #','Course Title','Units','Actv','Start - End','Instructor','Max Enrl', 'Act Enrl','Seats Avail'],axis = 1)
        temp = self.df['Time'].str.split(pat='-',expand=True)
        self.df['Start'] = pd.to_timedelta(pd.to_datetime(temp[0],format= '%H:%M').dt.hour, unit = 'h') + pd.to_timedelta(pd.to_datetime(temp[0],format= '%H:%M').dt.minute, unit = 'm')
        self.df['End'] = pd.to_timedelta(pd.to_datetime(temp[1].str[:-2],format= '%H:%M').dt.hour, unit = 'h') + pd.to_timedelta(pd.to_datetime(temp[1].str[:-2],format= '%H:%M').dt.minute,unit='m')
        self.df['meridiem'] = temp[1].str[-2:]
        self.df = self.df.drop('Time', axis = 1)

        twelve_hours = pd.Timedelta(12, unit='h')
        self.df['meridiem'] = pd.to_timedelta((self.df['meridiem'] == 'pm').astype(int) * 12, unit = 'h')
        self.df['End'] = self.df['End'] % twelve_hours + self.df['meridiem']
        self.df['period'] = self.df['End'] - self.df['Start']
        self.df['period'] = self.df['period'] > twelve_hours
        self.df['Start'] = self.df['Start'] + pd.to_timedelta(self.df['period'].astype(int) * 12, unit = 'h')
        self.df = self.df.drop(['meridiem','period'],axis=1)
        
    def find_room(self, day, start_str, end_str):
        temp = list(map(int, start_str.split(':')))
        start = pd.to_timedelta(temp[0], unit = 'h') + pd.to_timedelta(temp[1],unit = 'm')
        temp = list(map(int, end_str.split(':')))
        end = pd.to_timedelta(temp[0], unit = 'h') + pd.to_timedelta(temp[1],unit = 'm')
        
        occupied = self.df[self.df['Days'].str.contains(day)].copy()
        occupied = occupied[(occupied['Start'] > start) | (occupied['End'] < end)]
        occupied = occupied[(occupied['Start'] < end) | (occupied['End'] > start)]
        occupied = np.array(sorted(pd.unique(occupied['Bldg/Rm'])))
        idx_del = []
        for i in occupied:
            idx_del.append(int(np.where(self.room_list == i)[0]))
        available_rooms = np.delete(self.room_list, idx_del)

        self.available = available_rooms
        self.occupied = occupied
        return (available_rooms,occupied)

    def print(self):
        print(self.df)

if __name__ == "__main__":
    finder = roomfinder('.\class_schedule.xlsx')

    day = input("What day are you looking at (M/T/W/R/F)?\n:")
    start = input("From what time (military, HH:MM)?\n:")
    end = input("Until what time (military, HH:MM)?\n:")

    finder.find_room(day,start,end)
    print("Available rooms: ")
    print(finder.available)
    print("Occupied:")
    print(finder.occupied)