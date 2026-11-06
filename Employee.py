"""
# Employee.py
# Implementation of Calendar, Employee, and specialized subclasses (Faculty, Staff, Administrator, StudentWorker)
# Author: buonma98
"""

from Log import *

STATUS_AVAILABLE = "Available"
STATUS_AWAY = "Away"
STATUS_BUSY = "Busy"
STATUSES = (STATUS_AVAILABLE, STATUS_AWAY, STATUS_BUSY)


class Calendar:
    """
    **Calendar** models a simple schedule containing events for an office occupant.

    It allows an Administrator's availability to be automatically determined
    based on whether any active events or appointments are present.

    Parameters:
    ----------
    events : list of str, optional
        Initial list of scheduled events or calendar entries (default: None).

    Examples:
    ---------
    1. Check availability with no events (Available):
       ```python
       cal = Calendar()
       print(cal.getAvailability())  # 'Available'
       ```

    2. Check availability with meeting scheduled (Busy):
       ```python
       cal = Calendar(events=["Staff Meeting", "Budget Review"])
       print(cal.getAvailability())  # 'Busy'
       ```
    """

    def __init__(self, events=None):
        """
        Initialize the Calendar with an optional list of events.

        Parameters:
        ----------
        events : list of str, optional
            List of initial scheduled events (default: None).
        """
        self.events = list(events) if events is not None else []
        Log.i(f"Calendar initialized with {len(self.events)} events")

    def getAvailability(self):
        """
        Determine availability based on the presence of calendar events.

        Returns:
        -------
        str
            'Busy' if there are active events; otherwise 'Available'.
        """
        if self.events:
            return STATUS_BUSY
        return STATUS_AVAILABLE

    def __repr__(self):
        return f"<Calendar events={self.events}>"


class Employee:
    """
    **Employee** represents the base employee profile displayed on the digital NamePlate.

    Maintains standard employee identity and contact information, as well as an
    availability status that can be cycled manually for non-administrators. Provides
    a baseline `getDisplayInfo()` method designed to be overridden polymorphically.

    Parameters:
    ----------
    name : str
        Full name of the employee.
    position : str
        Job title or role.
    department : str, optional
        Department or unit name (default: "").
    email : str, optional
        Email address (default: "").
    phoneNumber : str, optional
        Contact phone number (default: "").
    availability : str, optional
        Initial availability status (default: 'Available').

    Examples:
    ---------
    1. Creating an employee and cycling availability:
       ```python
       emp = Employee("Alex Smith", "Coordinator", "Operations")
       print(emp.getAvailability())  # 'Available'
       emp.cycleAvailability()
       print(emp.getAvailability())  # 'Away'
       print(emp.getDisplayInfo())   # 'Coordinator'
       ```
    """

    def __init__(self, name, position, department="", email="", phoneNumber="", availability=STATUS_AVAILABLE):
        """
        Initialize an Employee instance.

        Parameters:
        ----------
        name : str
            Full name of the employee.
        position : str
            Job title or role.
        department : str, optional
            Department name (default: "").
        email : str, optional
            Email address (default: "").
        phoneNumber : str, optional
            Phone number (default: "").
        availability : str, optional
            Initial status (default: 'Available').
        """
        self.name = str(name)
        self.position = str(position)
        self.department = str(department)
        self.email = str(email)
        self.phoneNumber = str(phoneNumber)
        self.availability = availability if availability in STATUSES else STATUS_AVAILABLE
        Log.i(f"Employee initialized: {self.name} ({self.position}) - Status: {self.availability}")

    def getAvailability(self):
        """
        Return the employee's current availability status.

        Returns:
        -------
        str
            'Available', 'Away', or 'Busy'.
        """
        return self.availability

    def cycleAvailability(self):
        """
        Cycle availability status sequentially: Available -> Away -> Busy -> Available.
        """
        idx = STATUSES.index(self.availability) if self.availability in STATUSES else 0
        self.availability = STATUSES[(idx + 1) % len(STATUSES)]
        Log.i(f"Employee {self.name}: Cycled availability to '{self.availability}'")

    def getDisplayInfo(self):
        """
        Return custom information string formatted for the display.

        Returns:
        -------
        str
            Baseline information string (employee position).
        """
        return self.position

    def __repr__(self):
        return f"<{type(self).__name__} name='{self.name}', position='{self.position}', status='{self.getAvailability()}'>"


class Faculty(Employee):
    """
    **Faculty** specializes Employee with assigned teaching courses and office hours.

    Parameters:
    ----------
    name : str
        Full name of the faculty member.
    position : str, optional
        Job title (default: 'Faculty').
    department : str, optional
        Academic department (default: 'Academic').
    email : str, optional
        Email address (default: '').
    phoneNumber : str, optional
        Contact phone number (default: '').
    courses : list of str, optional
        List of course codes being taught (default: None).
    officeHours : str, optional
        Scheduled office hours (default: '').
    availability : str, optional
        Initial availability status (default: 'Available').

    Examples:
    ---------
    1. Creating a faculty member:
       ```python
       prof = Faculty("Dr. John Doe", courses=["COP4338", "CIS3931"], officeHours="MWF 10-12")
       print(prof.getDisplayInfo())  # 'COP4338 MWF 10-12'
       ```
    """

    def __init__(self, name, position="Faculty", department="Academic", email="",
                 phoneNumber="", courses=None, officeHours="", availability=STATUS_AVAILABLE):
        """
        Initialize a Faculty member.
        """
        super().__init__(name, position, department, email, phoneNumber, availability)
        self.courses = list(courses) if courses is not None else []
        self.officeHours = str(officeHours)
        Log.i(f"Faculty initialized: {self.name} | Courses: {self.courses} | Hours: {self.officeHours}")

    def getDisplayInfo(self):
        """
        Return course and office hours string for display.

        Returns:
        -------
        str
            Formatted course and office hours.
        """
        course_str = self.courses[0] if self.courses else "No Courses"
        if self.officeHours:
            return f"{course_str} {self.officeHours}"
        return course_str


class Staff(Employee):
    """
    **Staff** specializes Employee for general departmental staff members.

    Parameters:
    ----------
    name : str
        Full name of the staff member.
    position : str, optional
        Job title (default: 'Staff').
    department : str, optional
        Department name (default: '').
    email : str, optional
        Email address (default: '').
    phoneNumber : str, optional
        Contact phone number (default: '').
    availability : str, optional
        Initial availability status (default: 'Available').

    Examples:
    ---------
    1. Creating a staff member:
       ```python
       staff = Staff("Sarah Connor", department="IT Support")
       print(staff.getDisplayInfo())  # 'IT Support Staff'
       ```
    """

    def __init__(self, name, position="Staff", department="", email="", phoneNumber="", availability=STATUS_AVAILABLE):
        """
        Initialize a Staff member.
        """
        super().__init__(name, position, department, email, phoneNumber, availability)
        Log.i(f"Staff initialized: {self.name} ({self.department})")

    def getDisplayInfo(self):
        """
        Return staff department/role string for display.

        Returns:
        -------
        str
            Formatted staff information string.
        """
        if self.department:
            return f"{self.department} Staff"
        return self.position


class StudentWorker(Employee):
    """
    **StudentWorker** specializes Employee for student assistants working in the office.

    Parameters:
    ----------
    name : str
        Full name of the student worker.
    position : str, optional
        Job title (default: 'Student Worker').
    department : str, optional
        Assigned department (default: '').
    email : str, optional
        Email address (default: '').
    phoneNumber : str, optional
        Contact phone number (default: '').
    availability : str, optional
        Initial availability status (default: 'Available').

    Examples:
    ---------
    1. Creating a student worker:
       ```python
       student = StudentWorker("Emily Clark", department="Dean's Office")
       print(student.getDisplayInfo())  # 'Student Assistant'
       ```
    """

    def __init__(self, name, position="Student Worker", department="", email="",
                 phoneNumber="", availability=STATUS_AVAILABLE):
        """
        Initialize a StudentWorker.
        """
        super().__init__(name, position, department, email, phoneNumber, availability)
        Log.i(f"StudentWorker initialized: {self.name}")

    def getDisplayInfo(self):
        """
        Return student worker description string for display.

        Returns:
        -------
        str
            Formatted student worker role.
        """
        return "Student Assistant"


class Administrator(Employee):
    """
    **Administrator** specializes Employee with automatic calendar-driven availability.

    Delegates `getAvailability()` to its associated `Calendar` instance. Manual
    availability cycling is blocked by the NamePlate controller.

    Parameters:
    ----------
    name : str
        Full name of the administrator.
    position : str, optional
        Job title (default: 'Administrator').
    department : str, optional
        Department name (default: 'Administration').
    email : str, optional
        Email address (default: '').
    phoneNumber : str, optional
        Contact phone number (default: '').
    calendar : Calendar, optional
        Calendar instance used for automatic availability checks (default: None).
    availability : str, optional
        Default fallback availability status (default: 'Available').

    Examples:
    ---------
    1. Administrator with empty calendar (Available):
       ```python
       cal = Calendar()
       admin = Administrator("Dean Garcia", calendar=cal)
       print(admin.getAvailability())  # 'Available'
       print(admin.getDisplayInfo())   # 'Admin Office'
       ```

    2. Administrator with scheduled meeting (Busy):
       ```python
       cal_busy = Calendar(events=["Faculty Senate"])
       admin = Administrator("Dean Garcia", calendar=cal_busy)
       print(admin.getAvailability())  # 'Busy'
       ```
    """

    def __init__(self, name, position="Administrator", department="Administration",
                 email="", phoneNumber="", calendar=None, availability=STATUS_AVAILABLE):
        """
        Initialize an Administrator.
        """
        super().__init__(name, position, department, email, phoneNumber, availability)
        self.calendar = calendar
        Log.i(f"Administrator initialized: {self.name} | Calendar attached: {self.calendar is not None}")

    def getAvailability(self):
        """
        Return availability automatically retrieved from the Calendar.

        Returns:
        -------
        str
            'Available', 'Away', or 'Busy' from the Calendar; falls back to self.availability if no calendar.
        """
        if self.calendar is not None:
            return self.calendar.getAvailability()
        return self.availability

    def getDisplayInfo(self):
        """
        Return administrator office information for display.

        Returns:
        -------
        str
            Formatted administrative info string.
        """
        return "Admin Office"


if __name__ == "__main__":
    Log.i("Starting self-contained verification for Calendar and Employee hierarchy...")

    # 1. Test Calendar
    cal_empty = Calendar()
    assert cal_empty.getAvailability() == STATUS_AVAILABLE, "Empty calendar should be Available"

    cal_busy = Calendar(events=["Department Meeting"])
    assert cal_busy.getAvailability() == STATUS_BUSY, "Calendar with events should be Busy"

    # 2. Test base Employee
    emp = Employee("Alex Smith", "Coordinator", "Operations", "alex@fiu.edu", "305-555-0101")
    assert emp.name == "Alex Smith"
    assert emp.position == "Coordinator"
    assert emp.department == "Operations"
    assert emp.email == "alex@fiu.edu"
    assert emp.phoneNumber == "305-555-0101"
    assert emp.getAvailability() == STATUS_AVAILABLE
    assert emp.getDisplayInfo() == "Coordinator"

    # Test status cycling on regular employee
    emp.cycleAvailability()
    assert emp.getAvailability() == STATUS_AWAY, f"Expected Away, got {emp.getAvailability()}"
    emp.cycleAvailability()
    assert emp.getAvailability() == STATUS_BUSY, f"Expected Busy, got {emp.getAvailability()}"
    emp.cycleAvailability()
    assert emp.getAvailability() == STATUS_AVAILABLE, f"Expected Available, got {emp.getAvailability()}"

    # 3. Test Faculty subclass
    faculty = Faculty("Dr. Mark Miller", courses=["COP4338", "CIS3931"], officeHours="MWF 10-12")
    assert faculty.name == "Dr. Mark Miller"
    assert faculty.position == "Faculty"
    assert faculty.courses == ["COP4338", "CIS3931"]
    assert faculty.officeHours == "MWF 10-12"
    assert "COP4338 MWF 10-12" in faculty.getDisplayInfo(), f"Got {faculty.getDisplayInfo()}"

    # 4. Test Staff subclass
    staff = Staff("Sarah Connor", department="IT Support")
    assert staff.name == "Sarah Connor"
    assert staff.getDisplayInfo() == "IT Support Staff"

    # 5. Test StudentWorker subclass
    student = StudentWorker("Emily Clark", department="Dean's Office")
    assert student.name == "Emily Clark"
    assert student.getDisplayInfo() == "Student Assistant"

    # 6. Test Administrator subclass with Calendar
    admin_free = Administrator("Dean Garcia", calendar=cal_empty)
    assert admin_free.name == "Dean Garcia"
    assert admin_free.getAvailability() == STATUS_AVAILABLE, "Admin with empty calendar should be Available"
    assert admin_free.getDisplayInfo() == "Admin Office"

    admin_busy = Administrator("Dean Garcia", calendar=cal_busy)
    assert admin_busy.getAvailability() == STATUS_BUSY, "Admin with busy calendar should be Busy"

    Log.i("Testing complete - all checks passed for Calendar and Employee hierarchy")
