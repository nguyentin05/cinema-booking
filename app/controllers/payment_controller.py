from flask import Blueprint, render_template

payment_page = Blueprint("payment_page", __name__)


@payment_page.route("/stripe")
def stripe_payment():
    return render_template("payment/stripe.html")
