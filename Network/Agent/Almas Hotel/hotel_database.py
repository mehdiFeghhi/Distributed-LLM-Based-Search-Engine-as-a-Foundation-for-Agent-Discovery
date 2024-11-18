import sqlite3
from datetime import datetime

class HotelDatabase:
    def __init__(self, db_name='hotel_database.db'):
        self.db_name = db_name
        self._connect_to_database()

    def _connect_to_database(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self._check_tables_exist()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def _check_tables_exist(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rooms'")
        if self.cursor.fetchone() is None:
            self._create_tables()

    def _create_tables(self):
        """Creates the rooms and reservations tables if they don't exist"""
        self.cursor.execute('''
            CREATE TABLE rooms (
                room_number INTEGER PRIMARY KEY,
                room_type TEXT NOT NULL,
                beds TEXT NOT NULL,
                view TEXT NOT NULL,
                price INTEGER NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE reservations (
                room_number INTEGER,
                date_start DATE NOT NULL,
                date_end DATE NOT NULL,
                PRIMARY KEY (room_number, date_start),
                FOREIGN KEY (room_number) REFERENCES rooms (room_number)
            )
        ''')
        self.conn.commit()

    def insert_room(self, room_number, room_type, beds, view, price):
        """Inserts a new room into the rooms table"""
        self.cursor.execute('''
            INSERT INTO rooms (room_number, room_type, beds, view, price)
            VALUES (?,?,?,?,?)
        ''', (room_number, room_type, beds, view, price))
        self.conn.commit()

    def get_room(self, room_number):
        """Retrieves a room by room number"""
        self.cursor.execute('''
            SELECT * FROM rooms
            WHERE room_number =?
        ''', (room_number,))
        result = self.cursor.fetchone()
        if result:
            return {"room_number": result[0], "room_type": result[1], "beds": result[2], "view": result[3], "price": result[4]}
        else:
            return None

    def _validate_dates(self, date_start, date_end):
        """Validate that the reservation dates are after today"""
        today = datetime.now().date()
        if date_start < today or date_end < today:
            raise ValueError("Reservation dates must be after today's date.")
        if date_start >= date_end:
            raise ValueError("End date must be after the start date.")

    def insert_reservation(self, room_number, date_start, date_end):
        """Inserts a new reservation into the reservations table with date validation"""
        # Ensure date format and validation
        date_start = datetime.strptime(date_start, "%Y-%m-%d").date()
        date_end = datetime.strptime(date_end, "%Y-%m-%d").date()
        
        self._validate_dates(date_start, date_end)

        self.cursor.execute('''
            INSERT INTO reservations (room_number, date_start, date_end)
            VALUES (?,?,?)
        ''', (room_number, date_start, date_end))
        self.conn.commit()

    def get_reservation(self, room_number, date_start):
        """Retrieves a reservation by room number and date start"""
        self.cursor.execute('''
            SELECT * FROM reservations
            WHERE room_number =? AND date_start =?
        ''', (room_number, date_start))
        result = self.cursor.fetchone()
        if result:
            return {"room_number": result[0], "date_start": result[1], "date_end": result[2]}
        else:
            return None

    def delete_reservation(self, room_number, date_start):
        """Deletes a reservation by room number and date start"""
        self.cursor.execute('''
            DELETE FROM reservations
            WHERE room_number =? AND date_start =?
        ''', (room_number, date_start))
        self.conn.commit()

    def get_all_rooms(self):
        """Retrieves all rooms"""
        self.cursor.execute('''
            SELECT * FROM rooms
        ''')
        rows = self.cursor.fetchall()
        rooms = []
        for row in rows:
            room = {
                "room_number": row[0],
                "room_type": row[1],
                "beds": row[2],
                "view": row[3],
                "price": row[4]
            }
            rooms.append(room)
        return rooms

    def get_available_rooms(self, date_start, date_end):
        """Retrieves available rooms based on start and end dates"""
        # Ensure date format and validation
        date_start = datetime.strptime(str(date_start), "%Y-%m-%d").date()
        date_end = datetime.strptime(str(date_end), "%Y-%m-%d").date()

        self._validate_dates(date_start, date_end)

        self.cursor.execute('''
            SELECT * FROM rooms
            WHERE room_number NOT IN (
                SELECT room_number FROM reservations
                WHERE (date_start <= ? AND date_end >= ?)
            )
        ''', (date_end, date_start))
        rows = self.cursor.fetchall()
        available_rooms = []
        for row in rows:
            room = {
                "room_number": row[0],
                "room_type": row[1],
                "beds": row[2],
                "view": row[3],
                "price": row[4]
            }
            available_rooms.append(room)
        return available_rooms

    def close_connection(self):
        self.conn.close()

# Example usage
if __name__ == "__main__":
    hotel_db = HotelDatabase()

    # Add rooms data
    # rooms_data = [
    #     (101, "Standard", "2 Single Beds", "Sea View", 200),
    #     (102, "Standard", "1 Double Bed", "Garden View", 180),
    #     (103, "Standard", "2 Single Beds", "Garden View", 190),
    #     (104, "Standard", "1 Double Bed", "Sea View", 210),
    #     (201, "Suite", "1 King Bed", "Sea View", 350),
    #     (202, "Suite", "2 Queen Beds", "Sea View", 360),
    #     (203, "Suite", "1 King Bed", "Garden View", 340),
    #     (204, "Suite", "2 Queen Beds", "Garden View", 330),
    #     (301, "Luxury", "1 King Bed + Jacuzzi", "Sea View", 500),
    #     (302, "Luxury", "1 King Bed + Jacuzzi", "Garden View", 480),
    #     (303, "Luxury", "2 King Beds + Jacuzzi", "Sea View", 520),
    #     (304, "Luxury", "2 King Beds + Jacuzzi", "Garden View", 510),
    #     (401, "Standard", "2 Single Beds", "Sea View", 200),
    #     (402, "Standard", "1 Double Bed", "Garden View", 180),
    #     (403, "Standard", "2 Single Beds", "Garden View", 190),
    #     (404, "Standard", "1 Double Bed", "Sea View", 210),
    # ]

    # for room in rooms_data:
    #     hotel_db.insert_room(*room)

    # # Add reservation (example with valid dates after today)
    # try:
    #     hotel_db.insert_reservation(101, "2024-10-10", "2024-10-15")
    # except ValueError as ve:
    #     print(ve)

    # print(hotel_db.get_all_rooms())
    # print(hotel_db.get_available_rooms("2024-10-10", "2024-10-15"))
    # Add reservations (example with valid dates after today)
    # reservations_data = [
    #     (202, "2024-10-12", "2024-10-18"),
    #     (301, "2024-10-20", "2024-10-25"),
    #     (104, "2024-10-15", "2024-10-20"),
    #     (203, "2024-10-11", "2024-10-14"),
    #     (302, "2024-10-22", "2024-10-28"),
    # ]

    # for reservation in reservations_data:
    #     try:
    #         hotel_db.insert_reservation(*reservation)
    #     except ValueError as ve:
    #         print(ve)

    print(hotel_db.get_all_rooms())
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(hotel_db.get_available_rooms("2024-10-10", "2024-10-15"))

    hotel_db.close_connection()
    hotel_db.close_connection()
