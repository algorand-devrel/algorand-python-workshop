from algopy import Account, ARC4Contract, BoxMap, Global, Txn, UInt64, gtxn, itxn, Box, arc4, String
from algopy.arc4 import abimethod


class PersonalBank(ARC4Contract):

    def __init__(self) -> None:
        """Initializes contract storages on deployment.

        This BoxMap stores deposit amounts for each account.
        The BoxMap uses Account addresses as keys and UInt64 values to track deposited amounts.
        """
        self.depositors = BoxMap(Account, UInt64, key_prefix="")
        
        """Create box
        """
        
        self.github = Box(arc4.String, key=b"github")

    @abimethod()
    def deposit(self, pay_txn: gtxn.PaymentTransaction, github_handle: arc4.String) -> UInt64:
        """Deposits funds into the personal bank

        This method accepts a payment transaction and records the deposit amount in the sender's BoxMap.
        If the sender already has a deposit, the amount is added to their existing balance.

        Args:
            pay_txn: The payment transaction containing deposit information

        Returns:
            The total amount deposited by the sender after this transaction (as UInt64)
        """
        assert (
            pay_txn.receiver == Global.current_application_address
        ), "Receiver must be the contract address"
        assert pay_txn.amount > 0, "Deposit amount must be greater than zero"

        deposit_amt, deposited = self.depositors.maybe(pay_txn.sender)

        if deposited:
            self.depositors[pay_txn.sender] += pay_txn.amount
        else:
            self.depositors[pay_txn.sender] = pay_txn.amount
            
        self.github.value = github_handle

        return self.depositors[pay_txn.sender]

    @abimethod()
    def withdraw(self) -> UInt64:
        """Withdraws all funds from the sender's account

        This method transfers the entire balance of the sender's account back to them,
        and resets their balance to zero. The sender must have a deposit to withdraw.

        Returns:
            The amount withdrawn (as UInt64)
        """
        deposit_amt, deposited = self.depositors.maybe(Txn.sender)
        assert deposited, "No deposits found for this account"

        result = itxn.Payment(
            receiver=Txn.sender,
            amount=deposit_amt,
            fee=0,
        ).submit()

        self.depositors[Txn.sender] = UInt64(0)

        return result.amount
    
    @abimethod()
    def get_box(self) -> arc4.String:
        return self.github.value
