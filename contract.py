
import datetime
from math import ceil
from typing import Optional
from bill import Bill
from call import Call


# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This is an abstract class. Only subclasses should be instantiated.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: datetime.datetime
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class TermContract(Contract):
    """ A Term type contract for a phone line. Has better calling rate, but
    customer has to pay 300.00 deposit upon signing contract.
    This class inherits Contract superclass.

    === Public Attributes ===
    end:
        end date for the contract
    free_minutes:
                amount of free call minutes given to customer each month
    expired:
            indicated of whether end date of contract passed or not.
    """
    end: datetime.datetime
    free_minutes: int
    expired: bool

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        """ Create a new Term Contract with the <start> date, starts as
        inactive, and <end> date when contract is being terminated.
        This class inherits Contract superclass.
        """

        Contract.__init__(self, start)
        self.end = end
        self.free_minutes = TERM_MINS
        self.expired = False

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
            <year>. This may be the first month of the contract.
            Store the <bill> argument in this contract and set the appropriate
             rate per minute and fixed cost.
        """
        if self.start is not None:
            self.bill = bill
            self.bill.set_rates("TERM", TERM_MINS_COST)
            self.free_minutes = TERM_MINS
            if self.start.year == year and self.start.month == month:
                self.bill.add_fixed_cost(TERM_DEPOSIT + TERM_MONTHLY_FEE)
            else:
                self.bill.add_fixed_cost(TERM_MONTHLY_FEE)
            if self.end.month > month and self.end.year == year:
                self.expired = True

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.
        """
        duration = ceil(call.duration / 60.0)
        if self.free_minutes >= duration:
            self.bill.add_free_minutes(duration)
            self.free_minutes -= duration
        else:
            self.bill.add_free_minutes(self.free_minutes)
            duration -= self.free_minutes
            self.bill.add_billed_minutes(duration)
            self.free_minutes = 0

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
         with this contract.

         Precondition:
         - a bill has already been created for the month+year when this
          contract is being cancelled.
        """
        self.start = None
        if self.expired:
            return self.bill.get_cost() - TERM_DEPOSIT
        else:
            return self.bill.get_cost()


class MTMContract(Contract):
    """ A month-to-month type contract for a phone line. Has more expensive
     calling rate, customer doesn't have to pay deposit and there is no end
      date. This class inherits Contract superclass.
    """

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
           <year>. This may be the first month of the contract.
           Store the <bill> argument in this contract and set the appropriate
            rate per minute and fixed cost.
        """
        if self.start is not None:
            self.bill = bill
            self.bill.set_rates("MTM", MTM_MINS_COST)
            self.bill.add_fixed_cost(MTM_MONTHLY_FEE)


class PrepaidContract(Contract):
    """ A prepaid type contract for a phone line.

    === Public Attributes ===
    balance:
            amount of money customer has in his balance throughout month.
    """
    balance: float

    def __init__(self, start: datetime.date, balance: float) -> None:
        """ Create a new Term Contract with the <start> date, starts as
         inactive.
        """

        Contract.__init__(self, start)
        self.balance = -balance

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
           <year>. This may be the first month of the contract.
           Store the <bill> argument in this contract and set the appropriate
            rate per minute and fixed cost.
        """
        if self.start is not None:
            if self.bill is None:
                self.bill = bill
                self.bill.set_rates('PREPAID', PREPAID_MINS_COST)
                self.bill.add_fixed_cost(self.balance)
            else:
                self.balance = self.bill.get_cost()
                if self.balance > -10:
                    self.balance -= 25.00
                self.bill = bill
                self.bill.set_rates('PREPAID', PREPAID_MINS_COST)
                self.bill.add_fixed_cost(self.balance)

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
         with this contract.
        """
        self.start = None
        if self.bill is not None:
            if self.bill.get_cost() <= 0:
                return 0
            return self.bill.get_cost()
        else:
            return 0


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
