from typing import List, Optional, Protocol

from multiversx_sdk_core.errors import BadUsageError
from multiversx_sdk_core.interfaces import IAddress
from multiversx_sdk_core.tokens import TokenComputer, TokenTransfer
from multiversx_sdk_core.transaction import Transaction
from multiversx_sdk_core.transaction_factories.token_transfers_data_builder import \
    TokenTransfersDataBuilder
from multiversx_sdk_core.transaction_factories.transaction_builder import \
    TransactionBuilder


class IConfig(Protocol):
    chain_id: str
    min_gas_limit: int
    gas_limit_per_byte: int
    esdt_transfer: int
    esdt_nft_transfer: int
    multi_esdt_nft_transfer: int


class TransferTransactionsFactory:
    def __init__(self, config: IConfig) -> None:
        self.config = config
        self._data_args_builder = TokenTransfersDataBuilder()

    def create_transaction_for_native_token_transfer(self,
                                                     sender: IAddress,
                                                     receiver: IAddress,
                                                     native_amount: int,
                                                     data: Optional[str] = None) -> Transaction:
        transaction_data = data if data else ""
        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=receiver,
            data_parts=[transaction_data],
            gas_limit=0,
            add_data_movement_gas=True,
            amount=native_amount
        ).build()

    def create_transaction_for_esdt_token_transfer(self,
                                                   sender: IAddress,
                                                   receiver: IAddress,
                                                   token_transfers: List[TokenTransfer]) -> Transaction:
        if len(token_transfers) == 0:
            raise BadUsageError("No token transfers has been provided")

        transfer_args: List[str] = []
        extra_gas_for_transfer = 0

        token_computer = TokenComputer()

        if len(token_transfers) == 1:
            transfer = token_transfers[0]

            if token_computer.is_fungible(transfer.token):
                transfer_args = self._data_args_builder.build_args_for_esdt_transfer(transfer)
                extra_gas_for_transfer = self.config.esdt_transfer
            else:
                transfer_args = self._data_args_builder.build_args_for_single_esdt_nft_transfer(transfer, receiver)
                extra_gas_for_transfer = self.config.esdt_nft_transfer
                receiver = sender
        elif len(token_transfers) > 1:
            transfer_args = self._data_args_builder.build_args_for_multi_esdt_nft_transfer(receiver, token_transfers)
            extra_gas_for_transfer = self.config.multi_esdt_nft_transfer
            receiver = sender

        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=receiver,
            data_parts=transfer_args,
            gas_limit=extra_gas_for_transfer,
            add_data_movement_gas=True
        ).build()