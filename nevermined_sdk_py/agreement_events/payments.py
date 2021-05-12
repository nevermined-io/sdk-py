import logging

from contracts_lib_py.utils import process_fulfill_condition

from nevermined_sdk_py.nevermined.keeper import NeverminedKeeper as Keeper

logger = logging.getLogger(__name__)


def fulfill_lock_payment_condition(event, agreement_id, price, consumer_account, lock_condition_id):
    """
    Fulfill the lock reward condition.

    :param event: AttributeDict with the event data.
    :param agreement_id: id of the agreement, hex str
    :param price: Asset price, int
    :param consumer_account: Account instance of the consumer
    :param lock_condition_id: hex str the id of the lock reward condition for this `agreement_id`
    """
    if not event:
        logger.warning(
            f'`fulfill_lock_payment_condition` got empty event: event listener timed out.')
        return

    keeper = Keeper.get_instance()
    if keeper.condition_manager.get_condition_state(lock_condition_id) > 1:
        logger.debug(f'lock payment condition already fulfilled/aborted: '
                     f'agreementId={agreement_id}, lockPayment conditionId={lock_condition_id}')
        return

    logger.debug(f"about to lock payment (agreement {agreement_id}) after event {event}.")

    approved = keeper.token.token_approve(
        keeper.lock_payment_condition.address, price, consumer_account)
    logger.info(f'approval of token transfer was {"" if approved else "NOT"} successful')
    args = (
        agreement_id,
        keeper.escrow_payment_condition.address,
        price,
        consumer_account
    )
    process_fulfill_condition(args, keeper.lock_payment_condition, lock_condition_id, logger, keeper,
                              10)


fulfillLockRewardCondition = fulfill_lock_payment_condition
