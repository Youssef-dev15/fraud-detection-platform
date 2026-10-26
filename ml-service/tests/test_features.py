import pandas as pd
from app.features import add_features_v2


def make(**kw):
    base = {"type": "TRANSFER", "amount": 100.0,
            "oldbalanceOrg": 1000.0, "oldbalanceDest": 0.0}
    base.update(kw)
    return pd.DataFrame([base])


def test_account_emptied_when_amount_covers_balance():
    out = add_features_v2(make(amount=1000.0, oldbalanceOrg=1000.0))
    assert out.loc[0, "isAccountEmptied"] == 1


def test_account_not_emptied_on_partial_amount():
    out = add_features_v2(make(amount=100.0, oldbalanceOrg=1000.0))
    assert out.loc[0, "isAccountEmptied"] == 0


def test_zero_origin_balance_is_safe():
    out = add_features_v2(make(amount=50.0, oldbalanceOrg=0.0))
    assert out.loc[0, "isAccountEmptied"] == 0
    assert out.loc[0, "amountToBalanceRatio"] == 50.0


def test_destination_balance_ignored_outside_transfer():
    out = add_features_v2(make(type="CASH_OUT", oldbalanceDest=50000.0))
    assert out.loc[0, "oldbalanceDest"] == 0.0
    assert out.loc[0, "destWasEmpty"] == 1


def test_input_dataframe_is_not_mutated():
    df = make(type="CASH_OUT", oldbalanceDest=50000.0)
    add_features_v2(df)
    assert df.loc[0, "oldbalanceDest"] == 50000.0