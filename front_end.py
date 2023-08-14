import customtkinter as ctk
import datetime
import calendar as cal
from enum import StrEnum
from PIL import Image
import os
import json
import configparser
import back_end

config = configparser.ConfigParser()
config.read('settings.ini')
language_code = config['miscellaneous']['language']
text_json = json.load(open(f'locales/{language_code}.json', encoding='utf-8'))
default_planner_names = text_json['default planner names']

page = "Home"


class Colors(StrEnum):
    BLACK = "#231717"
    GREY = "#9CA2AE"
    DARK_GREY = "#303030"
    WHITE = "#FFFFFF"
    RED = "#FA5151"
    BLUE = "#4278E0"


date_today = datetime.date.today()
year_current = date_today.year
month_current = date_today.month
day_current = date_today.day
month_lookup = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                "November", "December"]

# initialise app
app = ctk.CTk()
app.geometry("800x600")
app.title("Canada Meal Planner")
app.iconbitmap(os.path.join("./images/cmp logo.ico"))
app.minsize(800, 600)
planner_selection = None


def search_entered(search_term=None):
    if search_term is None:
        search_term = search_entry.get()
    if search_term == "":
        return False
    # when the search button is entered, this function gets called,
    # which will get the data from the backend, and then forward it to the planner and some such function
    food_items = back_end.fuzzy_match(search_term)
    for suggestion_label, i in zip(suggestions_frame.grid_slaves(), range(9, -1, -1)):
        suggestion_label.configure(text=food_items[i])
        suggestion_label.bind("<Button-1>",
                              lambda e, food=suggestion_label.cget("text"): add_food_to_planner_slot(food))


def add_food_to_planner_slot(food):
    global planner_selection
    if planner_selection is not None:
        planner_new_entry_label = ctk.CTkLabel(planner_selection, text=food)
        planner_hour_length = len(planner_selection.grid_slaves())
        planner_selection.rowconfigure(planner_hour_length, weight=1)
        planner_new_entry_label.grid(column=0, row=planner_hour_length, sticky='w')
        # planner_hour_textbox = planner_selection.grid_slaves()[0]

def change_month(offset=0):
    global month_current, year_current
    month_current += offset
    if month_current <= 0:
        year_current -= 1
        month_current = 12
    if month_current >= 13:
        year_current += 1
        month_current = 1
    days = cal.monthrange(year_current, month_current)[1]
    calendar_month_year_label.configure(text=f"{month_lookup[month_current - 1]} {year_current}")
    slaves = calendar_days_frame.grid_slaves()
    for slave in slaves[0:31 - days]:
        slave.configure(fg_color=Colors.GREY, state="disabled")
    for slave in slaves[31 - days:31]:
        slave.configure(fg_color=Colors.BLUE, state="enabled")


def change_planner_focus(hf=None):
    global planner_selection
    if planner_selection is not None:
        planner_selection.configure(border_width=0)
    planner_selection = hf
    if hf is not None:
        hf.configure(border_width=3, border_color='#ff0000')


def regenerate_planner(plans: dict):
    # fill planner_scrollable_frame with that days entries, or placeholder text if there are none.
    global planner_selection
    planner_selection = None
    for planner_item in planner_scrollable_frame.grid_slaves():
        planner_item.grid_forget()
        planner_item.destroy()
    if not plans:
        for i in range(0 if plans else 4):
            hour_frame = ctk.CTkFrame(planner_scrollable_frame)
            hour_frame.bind("<Button-1>", lambda e=None, hf=hour_frame: change_planner_focus(hf))
            hour_frame.configure()
            planner_hour_name_entry = ctk.CTkEntry(hour_frame, height=20, font=('', 11),
                                                   placeholder_text='' if plans else default_planner_names[i])
            # planner_hour_food_entries = ctk.CTkTextbox(hour_frame, font=('', 11), state='disabled', wrap='word', activate_scrollbars=False)
            # planner_hour_food_entries.bind("<Button-1>", lambda e, hf=hour_frame: change_planner_focus(hf))
            if i % 2:
                hour_frame.configure(fg_color="#555555")
            hour_frame.columnconfigure(0, weight=1)
            hour_frame.rowconfigure(0, weight=1)
            # hour_frame.rowconfigure(1, weight=1)
            hour_frame.grid(column=0, row=i, sticky='ew')
            planner_hour_name_entry.grid(column=0, row=0, padx=3, pady=3, sticky='nw')
            # planner_hour_food_entries.grid(column=0, row=1, padx=3, pady=3, stick='ew')
    planner_add_button = ctk.CTkButton(planner_scrollable_frame, text='Add new')
    planner_add_button.grid(column=0, sticky='ew')


def change_day(day=day_current):
    # when a date is clicked on in the calendar, this function is called and will change the current day displayed
    global day_current
    day_current = day
    current_date_label.configure(text=f"{month_lookup[month_current - 1]} {day_current}")
    regenerate_planner({})


# Search Bar
def generate_search():
    global search_frame, search_entry, search_submit_button
    search_frame = ctk.CTkFrame(app, height=40)
    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search through Canada Meal Planner’s food catalogue..",
                                fg_color='#FA5151', border_width=0, text_color='#FFFFFF',
                                placeholder_text_color="#FFFFFF", font=('', 13))
    search_submit_button = ctk.CTkButton(search_frame, text="Search", command=search_entered)
    search_frame = ctk.CTkFrame(app, height=40)
    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search through Canada Meal Planner’s food catalogue..",
                                fg_color='#FA5151',
                                border_width=0, text_color='#FFFFFF', placeholder_text_color="#FFFFFF", font=('', 13))
    search_entry.bind("<Return>", lambda e: search_entered())
    search_submit_button = ctk.CTkButton(search_frame, text="Search", command=search_entered)
    search_frame.columnconfigure(0, weight=10)
    search_frame.columnconfigure(1, weight=1)
    search_entry.grid(column=0, row=0, sticky='ew')
    search_submit_button.grid(column=1, row=0, sticky='ew')


# suggestions
def generate_suggestions(): # IGNORE THE MISNOMER.
    global suggestions_frame, suggestion_label
    suggestions_frame = ctk.CTkFrame(app, height=60)
    for i in range(10):
        if i == 0:
            suggestion_label = ctk.CTkLabel(suggestions_frame,
                                            text="Use the search bar above to search for a food item. Suggestions will appear here.")
        elif i > 0:
            suggestion_label = ctk.CTkLabel(suggestions_frame, text="")
        suggestion_label.grid(column=i % 2, row=i // 2, sticky='nesw')
        suggestions_frame.columnconfigure(i % 2, weight=1)
        suggestions_frame.rowconfigure(i // 2, weight=1)


# calendar
def generate_calendar():
    global calendar_frame, calendar_month_frame, calendar_month_prior_button, calendar_month_following_button, calendar_month_year_label, calendar_days_frame
    calendar_frame = ctk.CTkFrame(app)
    calendar_month_frame = ctk.CTkFrame(calendar_frame, height=30)
    calendar_month_prior_button = ctk.CTkButton(calendar_month_frame, text="<", width=50)
    calendar_month_prior_button.bind("<Button-1>", lambda e: change_month(-1))
    calendar_month_following_button = ctk.CTkButton(calendar_month_frame, text=">", width=50)
    calendar_month_following_button.bind("<Button-1>", lambda e: change_month(1))
    calendar_month_year_label = ctk.CTkLabel(calendar_month_frame)
    calendar_days_frame = ctk.CTkFrame(calendar_frame)
    i = 0
    buttons = []
    for z in range(35):
        i += 1
        button = ctk.CTkButton(calendar_days_frame, text=str(i), command=lambda day=i: change_day(day))
        button.configure(width=50, height=50, font=("", 14), text_color=Colors.WHITE, text_color_disabled=Colors.WHITE)
        button.grid(column=z % 7, row=z // 7, padx=1, pady=1, sticky='nesw')
        calendar_days_frame.rowconfigure(z // 7, weight=1)
        calendar_days_frame.columnconfigure(z % 7, weight=1)
        if z % 7 == 6:
            button.grid(padx=(1, 10), sticky='nesw')
        if z % 7 == 0:
            button.grid(padx=(10, 1), sticky='nesw')
        if i <= 7:
            button.grid(pady=(10, 1), sticky='nesw')
        elif i >= 29:
            button.grid(pady=(1, 10), sticky='nesw')
        buttons.append(button)
        if i == 31:
            break
    calendar_frame.rowconfigure(0, weight=1)
    calendar_frame.rowconfigure(1, weight=8)
    calendar_frame.columnconfigure(0, weight=1)
    calendar_month_frame.grid(column=0, row=0)
    calendar_month_prior_button.grid(column=0, row=0)
    calendar_month_year_label.grid(column=1, row=0, padx=30)
    calendar_month_following_button.grid(column=2, row=0)
    calendar_days_frame.grid(column=0, row=1, sticky='new')


# Planner
def generate_planner():
    global planner_frame, current_date_label, planner_scrollable_frame, calendar_frame
    planner_frame = ctk.CTkFrame(app)
    current_date_label = ctk.CTkLabel(planner_frame, text=f"{month_lookup[month_current - 1]} {day_current}")
    planner_scrollable_frame = ctk.CTkScrollableFrame(planner_frame)
    planner_frame.columnconfigure(0, weight=1)
    planner_frame.rowconfigure(0, weight=1)
    planner_frame.rowconfigure(1, weight=8)
    current_date_label.grid(column=0, row=0, sticky='ew')
    planner_scrollable_frame.columnconfigure(0, weight=1)
    planner_scrollable_frame.grid(column=0, row=1, sticky='nesw')


def display_page(page="Home"):
    for slave in app.grid_slaves():
        slave.grid_forget()
    if page == "Home":
        app.columnconfigure(0, weight=1)
        app.columnconfigure(1, weight=5)
        app.columnconfigure(2, weight=5)
        app.columnconfigure(3, weight=5)
        app.rowconfigure(0, weight=1)
        app.rowconfigure(1, weight=1)
        app.rowconfigure(2, weight=8)
        app.rowconfigure(3, weight=2)
        icon_label.grid(column=0, row=0, pady=(4, 8))
        calendar_frame.grid(column=0, row=1, columnspan=2, sticky='new', rowspan=2)
        search_frame.grid(column=1, row=0, columnspan=3, padx=8, pady=8, sticky='ew')
        suggestions_frame.grid(column=2, row=1, columnspan=2, padx=8, pady=(0, 4), sticky='nesw')
        planner_frame.grid(column=2, row=2, columnspan=2, padx=8, sticky='nesw')
        footer_frame.grid(column=0, row=3, columnspan=4, sticky='nesw')
    elif page == "Recipe":
        print("recipe")
    elif page == "Profile":
        print("profile")
    elif page == "Leaderboard":
        print("leaderboard")
    else:
        display_page()
        return True

def generate_footer():
    global footer_frame
    footer_frame = ctk.CTkFrame(app)
    leaderboard_button = ctk.CTkButton(footer_frame, text="",
                                       image=ctk.CTkImage(Image.open("images/leaderboard.png"), size=(76, 73)),
                                       command=lambda: display_page("Leaderboard"))
    home_button = ctk.CTkButton(footer_frame, text="", image=ctk.CTkImage(Image.open("images/home.png"), size=(76, 73)),
                                command=lambda: display_page("Home"))
    recipe_button = ctk.CTkButton(footer_frame, text="",
                                  image=ctk.CTkImage(Image.open("images/recipe.png"), size=(76, 73)),
                                  command=lambda: display_page("Recipe"))
    profile_button = ctk.CTkButton(footer_frame, text="",
                                   image=ctk.CTkImage(Image.open("images/profile.png"), size=(76, 73)),
                                   command=lambda: display_page('Profile'))
    footer_frame.columnconfigure(0, weight=1)
    footer_frame.columnconfigure(1, weight=1)
    footer_frame.columnconfigure(2, weight=1)
    footer_frame.columnconfigure(3, weight=1)
    footer_frame.rowconfigure(0, weight=1)
    leaderboard_button.grid(column=0, row=0, ipady=6, sticky='ew')
    home_button.grid(column=1, row=0, ipady=6, sticky='ew')
    recipe_button.grid(column=2, row=0, ipady=6, sticky='ew')
    profile_button.grid(column=3, row=0, ipady=6, sticky='ew')

def generate_app():
    global icon_label
    cmp_icon = ctk.CTkImage(Image.open(os.path.join("images/cmp64.png")), size=(64, 64))
    icon_label = ctk.CTkLabel(app, image=cmp_icon, text='')
    generate_calendar()
    generate_planner()
    generate_search()
    generate_suggestions()
    generate_footer()
    change_month()
    change_day()

generate_app()
display_page()

app.mainloop()
