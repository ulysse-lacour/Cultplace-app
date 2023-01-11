# main.py

import json
import logging
import requests

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from flask import Blueprint, Response, flash, render_template, request
from flask_login import current_user, login_required
from ImageCharts import ImageCharts
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
from utils.utils import list_to_element_counted_and_sorted_dict
from werkzeug.exceptions import BadRequest, NotFound, Conflict, Forbidden
from project.models.service import Service
from project.models.product import Product
from project.settings import (
    APP_NAME,
    DB_ORM,
    LADDITION_AUTH_TOKEN,
    LADDITION_CUSTOMER_ID,
    SOWPROG_EMAIL_CREDENTIAL,
    SOWPROG_PASSWORD
)
from project.synchers import sowprog_syncher, ProductSyncher

main = Blueprint('main', __name__)
logger = logging.getLogger(APP_NAME)
PAGES_NUM_TO_LOAD = 10

ADMIN_ONLY_MESSAGE = 'Only a possessor of the True Force can enter this zone.'
MAJORATION_PRICES = {
    0: [
        'Bière Bouteille',
        'SHOT ',
        'SHOT supp',
        'APPIE BRUT',
        'APPIE POIRE',
        'APPIE ROSE',
        'CAIPI',
        'TI PUNCH',
        'CORONA',
        'CORONA',
        'GIN FIZZ',
        'CUBA LIBRE',
        'COCKTAILS  dimanche',
    ],
    0.5: [
        'V Chardonnay ',
        'Demi Blonde',
        'Demi Péroni',
        'Demi grolsch',
        'Demi IPA',
    ],
    1: [
        'SOFT verse',
        'Alcool PREM + Soft',
        'Alcool+Soft',
        'Virgin cocktails',
        'DEMI Autre',
        'Blonde pinte',
        'Pinte grolsch',
        'Pinte peroni',
        'Pinte IPA',
        'DEMI Blanche',
        'Demi St stef',
        'BUNDABERG',
        'MOSCOW MULE',
        'BUNDABERG',
        'DARK & STORMY',
        'REDBULL',
        'PINTE Autre',
    ],
    1.5: [
        'V Syrah',
        'V Rose',
        'Lemonaid',
        'Charitea ',
    ],
    2: [
        'BTL CHARDONAY ',
        'PINTE Blanche',
        'Pinte st stef',
        'MOJITO',
        'Weizen Pinte',
    ],
    3: [
        'SPRITZ ST GERMAIN',
        'COCKTAILS  classique'
    ],
    4: [
        'SPRITZ',
        'SPRITZ FIERO',
    ],
    7: [
        'BTL SYRAH ',
        'BTL Rose',
    ],
}


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@main.route('/admin')
@login_required
def admin():
    if current_user.super_user is True:
        return render_template('admin.html', user=current_user)
    else:
        flash(ADMIN_ONLY_MESSAGE)
        return render_template('profile.html', user=current_user)


# SERVICE INDEX
@main.route('/services', methods=['GET', 'POST'], defaults={"page": 1})
@main.route('/services/<int:page>', methods=['GET', 'POST'])
@login_required
def handle_services(page):
    page = page
    pages = PAGES_NUM_TO_LOAD
    if request.method == 'GET':
        services = (
            Service.query
            .order_by(Service.id.desc())
            .paginate(page, pages, error_out=False)
        )
    elif request.method == 'POST':
        # TODO RECUPERER DATE POUR FILTRE + RIEN EN FRONT

        services = (
            Service.query.filter(Service.date <= '2022-01-25')
            .filter(Service.date >= '2022-01-15')
            .paginate(
                page,
                pages,
                error_out=False,
            )
        )

        # FIXME: Dates should be serialized, and not set as a string.
    else:
        return BadRequest(f"Only POST and GET method are allowed, received {request.method}")

    return render_template('list_services.html', services=services)


@main.route('/add_service', methods=['POST'])
def add_service():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            new_service = Service(
                company=data['company'],
                date=data['date'],
                CA=data['CA'],
                solid=data['solid'],
                liquid=data['liquid'],
                majoration=data['majoration'],
                graph_url=data['graph_url'],
                top_liquids=data['top_liquids'],
                all_products_list_by_name=data['all_products_list_by_name'],
                all_products_timeline=data['all_products_timeline'],
                concert=data['concert'],
                concert_infos=data['concert_infos']
            )
            DB_ORM.session.add(new_service)
            DB_ORM.session.commit()
            return {"message": f"service {new_service.date} has been created successfully."}
        else:
            return {"error": "The request payload is not in JSON format"}
    else:
        return {"error": "The request is not a POST request"}


@main.route('/add_menu', methods=['GET', 'POST', 'DELETE'])
@login_required
def add_menu():
    products_added = None
    if request.method == 'GET':
        return render_template('menu.html', products_added=products_added)

    elif request.method == 'POST':

        products_added, updated_products = ProductSyncher.sync_products()

        return render_template(
            'menu.html',
            products_added=products_added,
            products_updated=updated_products,
        )

    elif request.method == 'DELETE':
        if current_user.super_user is True:
            # TODO : add delete menu
            flash("SOON")
            return render_template('admin.html')
        else:
            flash(ADMIN_ONLY_MESSAGE)
            return render_template('menu.html')


@main.route('/service/<int:service_id>', methods=['GET', 'POST', 'DELETE'])
@login_required
def handle_service(service_id):
    # return {"message": "TEST"} -> DELETEME
    service = Service.query.get_or_404(service_id)
    concert_dict = json.loads(service.concert_infos)
    concert_json = {
        "title": concert_dict.get("title"),
        "facebook": concert_dict.get("facebook"),
        "style": concert_dict.get("style"),
        "free": concert_dict.get("free"),  # is this a boolean ? if yes, please rename the key to 'is_free'
        "picture": concert_dict.get("picture"),  # is this a url ? you know what to do :p
    }
    if request.method == 'POST':
        select_info = request.form.get('select_info')
        input_value = request.form.get('select_value')
        select_concert_info = request.form.get('select_concert_info')
        select_concert_value = request.form.get('select_concert_value')
        select_is_free = request.form.get('select_is_free')

        if select_info == "CA":
            service.CA == input_value
        elif select_info == "liquid":
            service.liquid = input_value
        elif select_info == "solid":
            service.solid = input_value
        elif select_info == "majoration":
            service.majoration = input_value
        elif select_concert_info == "title" or select_concert_info == "style" or select_concert_info == "facebook":
            concert_json.update({select_concert_info: select_concert_value})
            service.concert_infos = json.dumps(concert_json)
        elif select_concert_info == "free":
            if not select_is_free:
                select_is_free = False
            concert_json.update({select_concert_info: select_is_free})
            service.concert_infos = json.dumps(concert_json)
        else:
            return {"message": "ERROR"}  # use one of werkzeug.exceptions and include information in description

        DB_ORM.session.add(service)
        DB_ORM.session.commit()

    elif request.method == 'DELETE':
        DB_ORM.session.delete(service)
        DB_ORM.session.commit()
        return {"message": f"Service {service.date} successfully deleted."}

    service = Service.query.get_or_404(service_id)
    # FIXME could youse service.serialize() to output a Json
    response = {
        "id": service.id,
        "company": service.company,
        "date": service.date.strftime('%d-%m-%Y'),
        "CA": service.CA,
        "solid": service.solid,
        "liquid": service.liquid,
        "majoration": service.majoration,
        "graph_url": service.graph_url,
        "top_liquids": service.top_liquids,
        "all_products_list_by_name": service.all_products_list_by_name,
        "all_products_timeline": service.all_products_timeline,
        "concert": service.concert,
        # vvv please don't json.loads multiple time. loads the dict in one hit.
        "title": json.loads(service.concert_infos)['title'],
        "facebook": json.loads(service.concert_infos)['facebook'],
        "style": json.loads(service.concert_infos)['style'],
        "free": json.loads(service.concert_infos)['free'],
        "picture": json.loads(service.concert_infos)['picture']
    }
    return render_template('service_details.html', service=response)


@main.route('/service/<int:service_id>/graph')
@login_required
def handle_graph(service_id):
    service = Service.query.get_or_404(service_id)
    if not service.graph_url:
        flash('No graph generated for this service.')
        response = {
            "date": service.date.strftime('%d %m %Y'),
            "graph_url": ""
        }
        return render_template('graph.html', service=response)
    else:
        response = {
            "id": service.id,
            "company": service.company,
            "date": service.date.strftime('%d-%m-%Y'),
            "CA": service.CA,
            "liquid": service.liquid,
            "graph_url": service.graph_url,
            "top_liquids": service.top_liquids
        }
        return render_template('graph.html', service=response)


@main.route('/service/<int:service_id>/json', methods=['GET', 'POST'])
@login_required
def json_tools_view(service_id):
    service = Service.query.get_or_404(service_id)
    if not service.all_products_timeline and not service.all_products_list_by_name:
        flash('No info for this in this service')
        return render_template(
            'json_tools.html',
            user=current_user,
            service=service,
            result_timeline="",
            result_product=""
        )

    product_name_to_profits = json.loads(service.all_products_list_by_name)

    command_datetime_to_profits = {
        datetime.fromisoformat(key): value
        for key, value in json.loads(service.all_products_timeline).items()
    }
    service = {
        "service_id": service_id,
        "date": service.date.strftime('%Y-%m-%d'),
        "title_date": service.date.strftime('%d-%m-%Y'),
        "graph_url": service.graph_url
    }

    products_to_search = [
        product_name
        for product_name in product_name_to_profits.keys()
    ]

    if request.method == 'GET':
        return render_template(
            'json_tools.html',
            user=current_user,
            service=service,
            products_to_search=products_to_search,
            result_timeline="",
            result_product=""
        )

    elif request.method == 'POST':
        if request.json["wich_json"] == 'timeline':
            input_date_start = datetime.strptime(
                request.json['input_date_start'].replace('T', ' '),
                '%Y-%m-%d %H:%M'
            )
            input_date_end = datetime.strptime(
                request.json['input_date_end'].replace('T', ' '),
                '%Y-%m-%d %H:%M'
            )
            result_timeline = 0

            for command_time, profits in command_datetime_to_profits.items():
                if (command_time > input_date_start and command_time < input_date_end):
                    for command_price in profits:
                        result_timeline += command_price
            result_timeline = round(result_timeline, 2)
            result_timeline = str(result_timeline) + " €"

            return result_timeline

        elif request.json['wich_json'] == 'product':
            product_to_search = request.json['products_to_search']
            result_product = 0
            for product_name, product_infos in product_name_to_profits.items():
                if product_name == product_to_search:

                    for command_info in product_infos:
                        for command_price in command_info.values():
                            result_product += command_price
            result_product = round(result_product, 2)
            result_product = str(result_product) + " €"

            return result_product


@main.route('/service/<int:service_id>/concert', methods=['GET', 'POST'])
def concert_view(service_id):
    service = Service.query.get_or_404(service_id)
    # TODO GERER NO CONCERT
    # if not service.concert:
    #     flash('No infos for this concert in this service')

    concert = {
        "id": service.id,
        "company": service.company,
        "date": service.date.strftime('%Y-%m-%d'),
        "title": json.loads(service.concert_infos)['title'],
        "facebook": json.loads(service.concert_infos)['facebook'],
        "style": json.loads(service.concert_infos)['style'],
        "free": json.loads(service.concert_infos)['free'],
        "picture": json.loads(service.concert_infos)['picture'],
    }
    return render_template('concert.html', concert=concert)


@main.route('/new_service/', methods=['GET'])
@login_required
def manually_add_service_page():
    return render_template('new_service.html')


@main.route("/request_service/", methods=["POST"])
@login_required
def request_manualy_add_service():
    date_with_no_sales = ""
    date_added_to_database = ""
    date_to_search = request.form.get('date_to_search')
    try:
        date_to_search = datetime.strptime(date_to_search, '%Y-%m-%d')
    except ValueError as e:
        return BadRequest(description="Wrong date format, use : DAY/MONTH/YEAR")

    log_extra = {
        "date_to_search": str(date_to_search),
    }

    period_start_date = date_to_search
    period_end_date = date_to_search + timedelta(days=1)
    date_to_search_str = date_to_search.strftime('%Y-%m-%d')

    concert_name, concert_infos, error = sowprog_syncher(date_to_search=date_to_search)

    # API L'ADDITION
    url = "https://api.laddition.com/ShiftDocuments"  # FIXME: Should be at least a constant on top of file
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {LADDITION_AUTH_TOKEN}"
    headers["customerid"] = LADDITION_CUSTOMER_ID
    params = CaseInsensitiveDict()
    params = (
        (
            'opening_date', '{} 15:00:00'.format(
                period_start_date.strftime('%Y-%m-%d')
            )
        ),
        (
            'closing_date', "{} 06:00:00".format(
                period_end_date.strftime('%Y-%m-%d')
            )
        ),
    )

    # REQUETE API POUR RECUPERER LE SERVICE
    laddition_response = requests.get(url, headers=headers, params=params)
    if laddition_response.json()["data"] != []:

        # INITIALISATION VARIABLES
        sales_details = laddition_response.json()["data"][0]
        service_id = sales_details['id']
        sales_no_tva = sales_details['amount_total_evat']
        liquids_no_tva = 0
        solids_no_tva = 0
        solids = CaseInsensitiveDict()
        solids["no_TVA"] = 0
        liquids = CaseInsensitiveDict()
        liquids["no_TVA"] = 0
        liquids["quantity"] = 0
        notfound = CaseInsensitiveDict()
        notfound["no_TVA"] = 0
        markup = CaseInsensitiveDict()
        markup["amount"] = 0
        markup["quantity"] = 0
        products_with_markup = []
        products_without_markup = []
        products_lacking_markup = []
        drinks_sold = []
        top5_most_sold_drinks = []
        all_products_by_timeline = defaultdict(list)
        all_products_by_name = defaultdict(list)

        # REQUETE API POUR RECUPERER LE NOMBRE DE PAGES
        service_reponse = requests.get(
            url + "/{}/SalesDocumentLines".format(service_id), headers=headers)
        last_page = service_reponse.json()["lastPage"]

        # PAGINATION
        for page in range(1, last_page + 1):

            # REQUETE API POUR RECUPERER LES PRODUITS VENDUS
            service_reponse = requests.get(
                url + "/{}/SalesDocumentLines?page={}".format(service_id, page), headers=headers)
            service_response = service_reponse.json()["data"]

            # BOUCLE DES PRODUITS VENDUS
            for service_data in service_response:
                # check if product alrealy in DB
                check_if_product_already_in_DB = Product.query.filter_by(
                    uniq_id_product=service_data['id_product']).count()
                if check_if_product_already_in_DB == 1:
                    product_in_DB = Product.query.filter_by(
                        uniq_id_product=service_data['id_product']
                    ).first()
                elif check_if_product_already_in_DB > 1:
                    return Conflict(description="Error in menu, more than 1 product find in menu")
                else:
                    return NotFound(description="Product not found, update Menu at cultplace.app/add_menu")

                # ALL PRODUCTS
                all_products_by_timeline[
                    service_data["timestamp_locale"]
                ].append(
                    service_data["amount_total_evat"]
                )
                all_products_by_name[
                    service_data["product_name"]
                ].append(
                    {
                        service_data["timestamp_locale"]: service_data["amount_total_evat"]
                    }
                )

                # SOLIDES HT
                if product_in_DB.category1 == "solid":
                    solids["no_TVA"] = solids["no_TVA"] + service_data["amount_total_evat"]

                # LIQUIDES HT
                elif product_in_DB.category1 == "liquid":
                    drinks_sold.append(service_data["product_name"])
                    liquids["no_TVA"] = liquids["no_TVA"] + \
                        service_data["amount_total_evat"]
                    liquids["quantity"] = liquids["quantity"] + 1

                    # MAJORATION
                    if service_data["category_name"] == "CONCERT":
                        product_hasnt_found_his_match = True
                        not_in_majoration_list = True
                        for price, name in MAJORATION_PRICES.items():
                            if service_data["product_name"] in name:
                                product_hasnt_found_his_match = False
                                not_in_majoration_list = False
                                markup["amount"] = markup["amount"] + price
                                markup["quantity"] += 1
                                products_with_markup.append(service_data["product_name"])
                                break

                        # THIS MIGHT BE OPTIONNAL, to investigate
                        if product_hasnt_found_his_match is True:
                            for price, name in MAJORATION_PRICES.items():
                                if service_data["product_type"] in name:
                                    product_hasnt_found_his_match = False
                                    not_in_majoration_list = False
                                    markup["amount"] = markup["amount"] + price
                                    markup["quantity"] += 1
                                    products_with_markup.append(service_data["product_name"])
                                    raise ValueError("Entered this logical branch that is probably not usefull")
                                    break
                        # ABOVE MAY BE OPTIONNAL

                        if not_in_majoration_list is True:
                            products_lacking_markup.append(service_data["product_name"])

                    else:
                        products_without_markup.append(service_data["product_name"])
                else:
                    notfound["no_TVA"] = notfound["no_TVA"] + service_data["amount_total_evat"]

        # DATA INGESTION
        products_with_markup = list_to_element_counted_and_sorted_dict(products_with_markup)
        products_with_markup["MAJORATION"] = {markup['quantity']: markup['amount']}
        products_without_markup = list_to_element_counted_and_sorted_dict(products_without_markup)
        products_lacking_markup = list_to_element_counted_and_sorted_dict(products_lacking_markup)
        drinks_sold = list_to_element_counted_and_sorted_dict(drinks_sold)

        top5_most_sold_drinks = list(drinks_sold.items())[:5]
        solids_no_tva = round(solids["no_TVA"], 2)
        liquids_no_tva = round(liquids["no_TVA"], 2)
        majoration_xls = round(markup["amount"], 2)
        sales_no_tva = round(sales_no_tva, 2)

        top5_most_sold_drinks = dict(top5_most_sold_drinks)
        top_5_boissons_vendues_values = ",".join(
            repr(e) for e in top5_most_sold_drinks.values()
        )
        top_5_boissons_vendues_values_for_chl = top_5_boissons_vendues_values.replace(
            ",", "|")
        top_5_boissons_vendues_keys = "|".join(
            repr(e) for e in top5_most_sold_drinks.keys())
        top_5_boissons_vendues_keys = top_5_boissons_vendues_keys.replace(
            "'", "")

        # PIE CHART FOR LIQUIDS
        pie_chart = (
            ImageCharts()
            .cht('pd')
            .chd("t:{}".format(top_5_boissons_vendues_values))
            .chdl("{}".format(top_5_boissons_vendues_keys))
            .chli("{} €".format(liquids_no_tva))
            .chl("{}".format(top_5_boissons_vendues_values_for_chl))
            .chtt("LIQUIDES HT (TOP 5)")
            .chdlp("l")
            .chs('400x200')
        )
        pie_chart_url = pie_chart.to_url()

        # INSCRIRE EN DB LE SERVICE
        # TODO : add majorationd details, produits non majores et produits a majorer in model
        new_service = Service(
            company='La Petite Halle',
            date=period_start_date.strftime('%Y-%m-%d'),
            CA=sales_no_tva,
            solid=solids_no_tva,
            liquid=liquids_no_tva,
            majoration=majoration_xls,
            graph_url=pie_chart_url,
            top_liquids=json.dumps(top5_most_sold_drinks),
            all_products_list_by_name=json.dumps(all_products_by_name),
            all_products_timeline=json.dumps(all_products_by_timeline),
            concert=concert_name,
            concert_infos=json.dumps(concert_infos),
        )
        DB_ORM.session.add(new_service)
        DB_ORM.session.commit()
        date_added_to_database = date_to_search_str
        logger.info(
            "Added 1 service: %s",
            new_service.id_str,
            extra={
                "service_data": new_service.serialize(),
            }
        )
    else:
        date_with_no_sales = date_to_search_str

    return Response(
        json.dumps(
            {
                "created_service": date_added_to_database,
            }
        ),
        status=200,
        content_type="application/json"
    )
