# =============================================================
# Drugs — Interactive Shiny Dashboard
# =============================================================
# Shiny for Python (official documentation):
#   - Homepage:    https://shiny.posit.co/py/
#   - Components:  https://shiny.posit.co/py/components/
#   - Layouts:     https://shiny.posit.co/py/layouts/
#   - Templates:   https://shiny.posit.co/py/templates/
#   - input_select:           https://shiny.posit.co/py/components/inputs/select-single/
#   - update_select (used to dynamically update dropdown choices):
#                             https://shiny.posit.co/py/api/core/ui.update_select.html
#   - layout_column_wrap:     https://shiny.posit.co/py/layouts/arrange/
#   - render.ui (dynamic UI): https://shiny.posit.co/py/components/outputs/ui/
#   - reactive.effect:        https://shiny.posit.co/py/api/core/reactive.effect.html
#   - reactive.calc:          https://shiny.posit.co/py/api/core/reactive.calc.html
#
# Class lectures ShinyLecture1, ShinyLecture2, ShinyLecture3
#
# Other libraries used:
#   - Plotly Express:   https://plotly.com/python/plotly-express/
#   - Matplotlib:       https://matplotlib.org/stable/api/pyplot_summary.html
#   - ipyleaflet:       https://ipyleaflet.readthedocs.io/en/latest/
#   - pandas:           https://pandas.pydata.org/docs/
#
# Techniques used beyond lecture material:
#   - Saving matplotlib figures to a memory buffer (BytesIO):
#       https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html
#   - base64 encoding in Python:
#       https://docs.python.org/3/library/base64.html
#   - Data URLs (embedding images inline as base64 PNGs):
#       https://developer.mozilla.org/en-US/docs/Web/URI/Schemes/data
# AI => Claude

from pathlib import Path
import base64
import io

from shiny import App, render, reactive, ui
import pandas as pd
import plotly.express as px
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
from shinywidgets import output_widget, render_widget


from ipyleaflet import Map, Marker, basemaps, basemap_to_tiles, CircleMarker
from ipywidgets import HTML

# -------------------------------------------------------------
# Load the cleaned dataset
# -------------------------------------------------------------
df = pd.read_csv("drug_consumption_clean.csv")

# Pre-compute key facts used on the welcome page
N_RESPONDENTS = df.shape[0]
N_DRUGS = 18
N_TRAITS = 7
N_LIARS_REMOVED = 8

# -------------------------------------------------------------
# Column groups
# -------------------------------------------------------------
PERSONALITY_COLS = [
    "Neuroticism", "Extraversion", "Openness",
    "Agreeableness", "Conscientiousness", "Impulsivity", "Sensation Seeking",
]

DRUG_COLS = [
    "Alcohol", "Amphetamines", "Amyl Nitrite", "Benzodiazepines",
    "Caffeine", "Cannabis", "Chocolate", "Cocaine", "Crack Cocaine",
    "Ecstasy", "Heroin", "Ketamine", "Legal Highs", "LSD",
    "Methamphetamine", "Magic Mushrooms", "Nicotine", "Volatile Substance Abuse",
]

FREQ_ORDER = [
    "Never Used", "Over a Decade Ago", "Last Decade",
    "Last Year", "Last Month", "Last Week", "Last Day",
]
FREQ_TO_NUM = {}
for i in range(len(FREQ_ORDER)):
    FREQ_TO_NUM[FREQ_ORDER[i]] = i

AGE_ORDER = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
EDUCATION_ORDER = [
    "Left school before 16 years",
    "Left school at 16 years",
    "Left school at 17 years",
    "Left school at 18 years",
    "Some college or university, no certificate or degree",
    "Professional certificate/ diploma",
    "University degree",
    "Masters degree",
    "Doctorate degree",
]

COLOR_MAPS = {
    "Age": {
        "18-24": "#1F77B4",
        "25-34": "#FF7F0E",
        "35-44": "#2CA02C",
        "45-54": "#D62728",
        "55-64": "#9467BD",
        "65+":   "#8C564B",
    },
    "Gender": {
        "Female": "#E377C2",
        "Male":   "#1F77B4",
    },
    "Education": {
        "Left school before 16 years":                          "#440154",
        "Left school at 16 years":                              "#3B528B",
        "Left school at 17 years":                              "#21908C",
        "Left school at 18 years":                              "#5DC863",
        "Some college or university, no certificate or degree": "#FDE725",
        "Professional certificate/ diploma":                    "#F89441",
        "University degree":                                    "#D8456C",
        "Masters degree":                                       "#9C179E",
        "Doctorate degree":                                     "#0D0887",
    },
    "Country": {
        "UK":                  "#1F77B4",
        "USA":                 "#D62728",
        "Canada":              "#FF7F0E",
        "Australia":           "#2CA02C",
        "Republic of Ireland": "#9467BD",
        "New Zealand":         "#17BECF",
        "Other":               "#7F7F7F",
    },
    "Ethnicity": {
        "White":             "#1F77B4",
        "Black":             "#2CA02C",
        "Asian":             "#FF7F0E",
        "Mixed-White/Black": "#9467BD",
        "Mixed-White/Asian": "#E377C2",
        "Mixed-Black/Asian": "#8C564B",
        "Other":             "#7F7F7F",
    },
}

# Country geo-coordinates for the map (Page 2).
# Used for the ipyleaflet markers.
COUNTRY_COORDS = {
    "UK":                  (54.0, -2.0),
    "USA":                 (39.5, -98.0),
    "Canada":              (56.0, -106.0),
    "Australia":           (-25.0, 134.0),
    "Republic of Ireland": (53.4, -7.9),
    "New Zealand":         (-41.0, 174.0),
    "Other":               None,
}

# Numeric drug usage frame for correlations (Page 4)
df_drug_numeric = pd.DataFrame()
for column_name in DRUG_COLS:
    df_drug_numeric[column_name] = df[column_name].map(FREQ_TO_NUM)

drug_choices = {}
for drug_name in DRUG_COLS:
    drug_choices[drug_name] = drug_name

trait_choices = {}
for trait_name in PERSONALITY_COLS:
    trait_choices[trait_name] = trait_name

# UI
app_ui = ui.page_navbar(

    # ---------- PAGE 1: WELCOME ----------
    ui.nav_panel(
        "Introduction",

        ui.h1("Introduction"),
        ui.p(
            "This is an interactive website focusing on drug consumption."
            " All information are real based and not synthetic."
            " Artificial intelligence was used to determine coordinates for the map, assist with map creation, help synchronize two dropdown menus, assist with colors, synchronize the explanation box, create a checkbox for a specific chart, generate text for the Personalities and Drugs page and the Drug Information page, clean up the code, and add comments to it."
        ),

        ui.h3("About original dataset"),
        ui.p(
            "The data comes from a survey of 1,884 anonymous respondents, "
            "collected by Fehrman et al. (2015) and made publicly available. The dataset also included 18 different drugs and 1 that was fake. "
            "Each participant answered questions regarding the use of 19 different drugs. "
            "They also described these personality traits to us and explained why they had chosen them. These traits were then measured. They include traits from the Big Five model, as well as impulsivity and the seeking of stimulation."
        ),
        ui.h3("Key facts of clean dataset"),
        ui.layout_column_wrap(
            ui.card(ui.card_header("Respondents"),         ui.h2(f"{N_RESPONDENTS:,}")),
            ui.card(ui.card_header("Substances tracked"),  ui.h2(f"{N_DRUGS}")),
            ui.card(ui.card_header("Personality traits"),  ui.h2(f"{N_TRAITS}")),
            ui.card(ui.card_header("Liars caught & removed"), ui.h2(f"{N_LIARS_REMOVED}")),
            width=1/4,
        ),

        ui.p(
            "As mentioned earlier, this dataset contains one fake drug. It was therefore decided that respondents who had ever used this drug would be removed from the dataset. "
            "While it is possible that the respondents simply made a mistake, this cannot be verified, therefore the final decision was that the respondents should not be included."
        ),

        ui.h3("How to use this app"),
        ui.tags.ul(
            ui.tags.li(ui.tags.b("Who Took Part?"),       " — explore the demographics of survey respondents."),
            ui.tags.li(ui.tags.b("Drug Explorer"),        " — pick a drug and see how its usage breaks down by age, gender, country and education."),
            ui.tags.li(ui.tags.b("Personality & Drugs"),  " — discover how seven personality traits relate to substance use."),
            ui.tags.li(ui.tags.b("Drug Information"),     " — a reference page explaining what each substance is and its legal status."),
        ),

        ui.h3("Important limitations"),
        ui.p(
            "A significant disadvantage of this dataset is the uneven representation of respondents in terms of nationality and ethnicity. More than half of the data comes from the UK (55%), followed by the US (29%), and the majority of respondents are white."
            "Another potential limitation could be bias. This is based on self reports, which even after removing the 8 respondents who provided false information, may not always reflect the truth."
        ),

        ui.hr(),
        ui.p(
            ui.tags.small(
                "Data source: Fehrman, E., Egan, V., & Mirkes, E. (2015). "
                "Drug Consumption (Quantified). UCI Machine Learning Repository. "
            ),
            ui.tags.a(
                "View original dataset",
                href="https://archive.ics.uci.edu/dataset/373/drug+consumption+quantified",
                target="_blank",
            ),
        ),
    ),

    # ---------- PAGE 2: WHO TOOK PART? ----------
    ui.nav_panel(
        "Who Took Part?",
        ui.h2("Who took part?"),
        ui.p("This page shows which age, national, educational, racial, and ethnic groups were involved. "), 

        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select(
                    "demo_show",
                    "Show me",
                    choices={
                        "Age": "Age",
                        "Gender": "Gender",
                        "Education": "Education",
                        "Country": "Country",
                        "Ethnicity": "Ethnicity",
                    },
                    selected="Age",
                ),
                # 'Split by' choices are dynamically updated in the server
                # so the user cannot pick the same variable as 'Show me'
                ui.input_select(
                    "demo_split",
                    "Split by (optional)",
                    choices={"None": "none"},
                    selected="None",
                ),
            ),
            # Top: chart
            ui.card(
                ui.card_header("Demographic breakdown"),
                output_widget("demo_plot"),
            ),
            # Map: ipyleaflet world map with mini-chart popups
            ui.card(
                ui.card_header("Where respondents are from"),
                output_widget("demo_map"),
                ui.tags.small(
                    "Click any circle to see that country's demographics in a popup.",
                    style="color: #888; padding: 0 0.5rem 0.5rem;",
                ),
            ),
        ),
    ),

    # ---------- PAGE 3: DRUG EXPLORER ----------
    ui.nav_panel(
        "Drug Explorer",
        ui.h2("Drug explorer"),
        ui.p("This page focuses on comparing age, gender, country, and education in relation to drug use."),  

        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select(
                    "drug_pick",
                    "Drug",
                    choices=drug_choices,
                    selected="Alcohol",
                ),
                # 'Compare with' choices are dynamically updated in the server
                # so the user cannot pick the same drug as 'Drug'
                ui.input_select(
                    "drug_compare",
                    "Compare with (optional)",
                    choices={"None": "none"},
                    selected="None",
                ),
                ui.input_radio_buttons(
                    "drug_breakdown",
                    "Break down by",
                    choices={
                        "Age": "Age",
                        "Gender": "Gender",
                        "Country": "Country (UK vs USA)",
                        "Education": "Education",
                    },
                    selected="Age",
                ),
                ui.hr(),
                # Per-chart toggles for whether to apply 'Compare with'
                ui.h6("Apply 'Compare with' to:"),
                ui.input_checkbox("apply_compare_breakdown", "Breakdown chart", False),
                ui.input_checkbox("apply_compare_summary",   "Active vs never used", False),
            ),
            ui.layout_column_wrap(
                ui.card(
                    ui.card_header("Frequency distribution"),
                    output_widget("drug_freq_plot"),
                ),
                ui.card(
                    ui.card_header("Breakdown chart"),
                    output_widget("drug_breakdown_plot"),
                ),
                width=1/2,
            ),
            ui.card(
                ui.card_header("Active vs never used"),
                output_widget("drug_summary_plot"),
            ),
        ),
    ),

    # ---------- PAGE 4: PERSONALITY & DRUGS ----------
    # Order: drill-down (violin plot) on top, heatmap below
    ui.nav_panel(
        "Personality & Drugs",
        ui.h2("Personality & drugs"),
        ui.p("This page shows the correlation between personality traits and drugs. The correlation heatmap provides a quick overview of what to focus on. "
             "Big Five descriptions based on the Five Factor Model (McCrae & Costa, 1987). Impulsivity (BIS-11: Patton et al., 1995) and Sensation Seeking (ImpSS: Zuckerman, 1994) were added by Fehrman et al. for this dataset."
             ),

        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select(
                    "pers_trait",
                    "Personality trait",
                    choices=trait_choices,
                    selected="Sensation Seeking",
                ),
                ui.input_select(
                    "pers_drug",
                    "Drug",
                    choices=drug_choices,
                    selected="Alcohol",
                ),
            ),
            # Top: drill-down (violin)
            ui.card(
                ui.card_header("Drill-down: selected trait vs selected drug"),
                output_widget("pers_drilldown"),
            ),
            # Glossary: explains the currently selected personality trait
            ui.card(
                ui.card_header("About this personality trait"),
                ui.output_ui("trait_glossary"),
            ),
            # Bottom: full heatmap
            ui.card(
                ui.card_header("Correlation heatmap — all traits vs all drugs"),
                output_widget("corr_heatmap"),
            ),
        ),
    ),

    # ---------- PAGE 5: DRUG INFORMATION ----------
    ui.nav_panel(
        "Drug Information",
        ui.h2("Drug information"),
        ui.p("This page contains descriptive information about all the drugs included in the dataset."),

        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select(
                    "info_drug",
                    "Pick a drug",
                    choices=drug_choices,
                    selected="Alcohol",
                ),
            ),
            ui.card(
                ui.card_header(ui.output_text("info_title")),
                ui.output_ui("info_content"),
            ),
        ),
    ),

    title="Drugs",
)


# =============================================================
# PERSONALITY TRAIT GLOSSARY (Page 4)
TRAIT_INFO = {
    "Neuroticism": {
        "model": "Big Five",
        "summary": "Tendency to experience negative emotions like anxiety, worry, sadness, and stress.",
        "high":    "Often anxious, easily upset, mood swings, sensitive to criticism, more likely to feel stressed under pressure.",
        "low":     "Calm, emotionally stable, handles stress well, doesn't get rattled easily, generally even-tempered.",
    },
    "Extraversion": {
        "model": "Big Five",
        "summary": "How much someone draws energy from being around other people and external stimulation.",
        "high":    "Outgoing, talkative, assertive, enjoys parties and crowds, energetic.",
        "low":     "Reserved, prefers quiet environments, finds large groups draining, enjoys time alone.",
    },
    "Openness": {
        "model": "Big Five",
        "summary": "Curiosity, creativity, and willingness to try new experiences and ideas.",
        "high":    "Imaginative, intellectually curious, attracted to art and unconventional ideas, enjoys novelty.",
        "low":     "Practical, traditional, prefers familiar routines, more conservative in tastes.",
    },
    "Agreeableness": {
        "model": "Big Five",
        "summary": "Tendency to be cooperative, trusting, and considerate towards others.",
        "high":    "Kind, helpful, trusting, prioritises harmony, considerate of others' feelings.",
        "low":     "Competitive, sceptical, more willing to challenge others, prioritises self-interest.",
    },
    "Conscientiousness": {
        "model": "Big Five",
        "summary": "Self-discipline, organisation, and being careful or thorough.",
        "high":    "Organised, disciplined, plans ahead, reliable, follows through on commitments.",
        "low":     "Spontaneous, flexible, dislikes rigid plans, may procrastinate.",
    },
    "Impulsivity": {
        "model": "BIS-11 scale (added by the researchers)",
        "summary": "Tendency to act on the spur of the moment without thinking through consequences.",
        "high":    "Acts quickly without much thought, makes snap decisions, struggles to delay gratification.",
        "low":     "Thinks carefully before acting, considers consequences, can wait for rewards.",
    },
    "Sensation Seeking": {
        "model": "ImpSS scale (added by the researchers)",
        "summary": "Need for varied, novel, and intense experiences — even if risky.",
        "high":    "Seeks thrills and adventure, drawn to risky activities, easily bored by routine.",
        "low":     "Prefers calm and predictable activities, avoids risk, comfortable with routine.",
    },
}




# =============================================================
# DRUG INFO
DRUG_INFO = {
    "Alcohol": {
        "category": "Depressant",
        "legal": "Legal in the UK for adults aged 18+. Sale to under-18s is prohibited.",
        "description": "Ethanol is a sedative produced by fermentation. It is the most widely used recreational drug in the world, consumed in beer, wine and spirits, and lowers inhibitions while impairing coordination and judgement.",
        "risks": "Short-term: impaired judgement, accidents, alcohol poisoning. Long-term: dependence, liver disease, cardiovascular problems, increased cancer risk, mental health effects.",
        "image": "images/alcohol.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Alcoholic_beverage#/media/File:Common_alcoholic_beverages.jpg",
    },
    "Amphetamines": {
        "category": "Stimulant",
        "legal": "Class B controlled drug in the UK (Misuse of Drugs Act 1971). Up to 5 years' imprisonment for possession.",
        "description": "Synthetic stimulants (commonly known as 'speed') that increase alertness, energy and focus by boosting dopamine and noradrenaline activity. Some forms are prescribed for ADHD and narcolepsy under medical supervision.",
        "risks": "Heart strain, raised blood pressure, anxiety, paranoia, insomnia and psychosis with heavy use. Dependence and severe comedowns are common. Risk of overdose, especially when mixed with other substances.",
        "image": "images/amphetamines.jpg",
        "image_credit": "https://adf.org.au/drug-facts/amphetamines/",
    },
    "Amyl Nitrite": {
        "category": "Vasodilator (commonly called 'poppers')",
        "legal": "Not controlled under the Misuse of Drugs Act 1971 in the UK. Possession is legal, although sale for human consumption is restricted under the Medicines Act 1968.",
        "description": "A volatile liquid inhaled for a brief 'rush' lasting a minute or two. It works by dilating blood vessels and relaxing smooth muscle, originally developed in the 19th century to treat angina.",
        "risks": "Headaches, dizziness, fainting and skin irritation around the nose and mouth. Dangerous when combined with erectile-dysfunction medication or other vasodilators. Highly flammable. Swallowing rather than inhaling can be fatal.",
        "image": "images/amyl_nitrite.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Poppers",
    },
    "Benzodiazepines": {
        "category": "Depressant / sedative",
        "legal": "Class C controlled drug in the UK. Legal with a prescription; possession without one is an offence.",
        "description": "Prescription sedatives such as diazepam (Valium) and alprazolam (Xanax), used medically to treat anxiety, insomnia and seizures. They enhance the calming effect of the GABA neurotransmitter.",
        "risks": "Strong dependence potential, even after short-term use. Withdrawal can be severe and dangerous. Highly risky when combined with alcohol or opioids — a leading cause of accidental overdose deaths.",
        "image": "images/benzodiazepines.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Benzodiazepine",
    },
    "Caffeine": {
        "category": "Stimulant",
        "legal": "Legal and unregulated. Found in coffee, tea, chocolate, energy drinks and many soft drinks.",
        "description": "The world's most widely consumed psychoactive substance. It blocks adenosine receptors in the brain, reducing the feeling of tiredness and increasing alertness and concentration.",
        "risks": "Mild dependence with regular use. High doses cause anxiety, jitters, insomnia, increased heart rate and digestive issues. Withdrawal symptoms include headaches and fatigue.",
        "image": "images/caffeine.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Energy_drink",
    },
    "Cannabis": {
        "category": "Depressant / mild hallucinogen",
        "legal": "Class B controlled drug in the UK. Up to 5 years' imprisonment for possession; up to 14 years for supply.",
        "description": "A plant-derived drug containing THC and CBD, usually smoked or eaten. Effects include relaxation, altered perception and an increased appetite. Medicinal cannabis is available on prescription in limited cases.",
        "risks": "Impaired memory and concentration, anxiety and paranoia, especially with stronger varieties. Long-term heavy use is linked to dependence and an increased risk of psychotic illness in vulnerable users. Smoking it carries respiratory risks.",
        "image": "images/cannabis.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Cannabis_%28drug%29",
    },
    "Chocolate": {
        "category": "Mild stimulant (food)",
        "legal": "Legal and unregulated.",
        "description": "Made from cocoa beans, chocolate contains small amounts of caffeine and theobromine — a mild stimulant chemically related to caffeine. It also triggers the release of endorphins, contributing to its mood-lifting effect.",
        "risks": "Generally low risk in moderation. Excessive consumption contributes to weight gain, dental problems and elevated cholesterol. Can be fatally toxic to dogs and cats.",
        "image": "images/chocolate.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Chocolate",
    },
    "Cocaine": {
        "category": "Stimulant",
        "legal": "Class A controlled drug in the UK. Up to 7 years' imprisonment for possession; up to life for supply.",
        "description": "A powerful stimulant derived from the coca plant, usually taken as a white powder snorted through the nose. It produces short-lived feelings of euphoria, confidence and energy by flooding the brain with dopamine.",
        "risks": "Heart attack, stroke and seizure even in healthy users. Strong psychological dependence, anxiety, paranoia and severe comedowns. Damages the nasal passages with regular use.",
        "image": "images/cocaine.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/File:CocaineHydrochloridePowder.jpg",
    },
    "Crack Cocaine": {
        "category": "Stimulant",
        "legal": "Class A controlled drug in the UK. Same penalties as cocaine.",
        "description": "A smokable form of cocaine, processed into crystalline 'rocks'. The high comes on within seconds and is much more intense but shorter than powder cocaine, lasting only a few minutes.",
        "risks": "Considered one of the most addictive forms of cocaine. The intense, short high drives compulsive redosing. Major risk of heart and lung problems, severe psychological dependence and rapid social and financial harm.",
        "image": "images/crack_cocaine.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Crack_cocaine",
    },
    "Ecstasy": {
        "category": "Stimulant / mild hallucinogen",
        "legal": "Class A controlled drug in the UK (active ingredient MDMA). Up to 7 years' imprisonment for possession.",
        "description": "MDMA, usually sold as pills or powder. Produces feelings of euphoria, emotional warmth and heightened sensory perception. Strongly associated with dance music and club culture since the 1980s.",
        "risks": "Dehydration, overheating and dangerously low blood sodium from drinking too much water. Pill content is unpredictable and may contain stronger or harmful substitutes. Linked to serotonin depletion and depression in heavy users.",
        "image": "images/ecstasy.jpg",
        "image_credit": "https://gpe.wikipedia.org/wiki/MDMA",
    },
    "Heroin": {
        "category": "Depressant / opioid",
        "legal": "Class A controlled drug in the UK. Up to 7 years' imprisonment for possession; up to life for supply.",
        "description": "A highly addictive opioid derived from morphine, usually injected, smoked or snorted. Produces intense pain relief and a feeling of euphoria followed by drowsiness.",
        "risks": "One of the most addictive drugs known. High overdose risk, especially when mixed with other depressants. Injecting carries serious infection risks (HIV, hepatitis, abscesses). Heroin overdoses kill more people than any other illegal drug in the UK.",
        "image": "images/heroin.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Heroin",
    },
    "Ketamine": {
        "category": "Dissociative anaesthetic",
        "legal": "Class B controlled drug in the UK (reclassified from Class C in 2014). Up to 5 years' imprisonment for possession.",
        "description": "Originally developed as a veterinary and human anaesthetic, ketamine produces dissociation — a sense of detachment from one's body and surroundings. Higher doses cause the so-called 'K-hole' experience.",
        "risks": "Severe and irreversible bladder damage with long-term use ('ketamine bladder'). Risk of accidents and assault while dissociated. Can cause memory problems, depression and dependence.",
        "image": "images/ketamine.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Ketamine",
    },
    "Legal Highs": {
        "category": "Various — synthetic novel psychoactive substances",
        "legal": "Production, sale and supply prohibited under the UK Psychoactive Substances Act 2016. Possession is generally not an offence except in custodial institutions.",
        "description": "An umbrella term for synthetic substances designed to mimic the effects of established drugs (such as cannabis, cocaine or ecstasy) while attempting to evade existing drug laws. Examples include Spice and mephedrone.",
        "risks": "Effects, strength and contents are highly unpredictable. Many are stronger or more harmful than the drugs they mimic. Linked to severe physical and mental health emergencies, dependence and several deaths in the UK.",
        "image": "images/legal_highs.jpg",
        "image_credit": "https://www.theguardian.com/society/2017/apr/24/the-legal-highs-ban-one-year-on-what-are-your-experiences",
    },
    "LSD": {
        "category": "Hallucinogen",
        "legal": "Class A controlled drug in the UK. Up to 7 years' imprisonment for possession.",
        "description": "Lysergic acid diethylamide, a powerful hallucinogen first synthesised in 1938. Usually taken as drops on small paper squares. Effects last 8–12 hours and include intense visual distortions, altered thinking and mood changes.",
        "risks": "Bad trips can cause severe anxiety, panic and frightening hallucinations. Risk of accidents while disoriented. Can trigger lasting mental health problems in vulnerable users (HPPD — persistent visual disturbances). Not considered physically addictive.",
        "image": "images/lsd.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/LSD",
    },
    "Methamphetamine": {
        "category": "Stimulant",
        "legal": "Class A controlled drug in the UK (reclassified from Class B in 2007). Up to 7 years' imprisonment for possession.",
        "description": "A powerful synthetic stimulant ('crystal meth') usually smoked, snorted or injected. Produces an intense, long-lasting high marked by extreme energy, alertness and euphoria.",
        "risks": "Highly addictive. Severe dental damage ('meth mouth'), skin sores, weight loss, paranoia and psychosis. Long-term use causes lasting brain changes. High risk of overdose and cardiovascular collapse.",
        "image": "images/methamphetamine.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Methamphetamine",
    },
    "Magic Mushrooms": {
        "category": "Hallucinogen",
        "legal": "Class A controlled drug in the UK (active ingredient psilocybin). Up to 7 years' imprisonment for possession.",
        "description": "Naturally occurring fungi containing psilocybin, which the body converts into psilocin. Effects are similar to LSD but typically shorter (4–6 hours), including visual changes, altered mood and shifts in perception.",
        "risks": "Bad trips, panic and confusion. Risk of accidents while disoriented. Real danger of misidentifying the species and eating poisonous lookalikes. Can trigger lasting issues in vulnerable users. Not considered physically addictive.",
        "image": "images/magic_mushrooms.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Psilocybin",
    },
    "Nicotine": {
        "category": "Stimulant",
        "legal": "Legal in the UK for adults aged 18+. Sale to under-18s prohibited.",
        "description": "The active ingredient in tobacco and most vaping products. Acts on the brain's nicotinic receptors to produce mild stimulation, focus and a sense of relaxation in habitual users.",
        "risks": "Highly addictive. Smoked tobacco is one of the leading causes of preventable death worldwide, linked to lung cancer, heart disease, stroke and many other illnesses. Vaping carries lower but not zero long-term risks.",
        "image": "images/nicotine.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Nicotine",
    },
    "Volatile Substance Abuse": {
        "category": "Inhalant",
        "legal": "The substances themselves (aerosols, glues, solvents, gas lighter refills) are legal. It is an offence in the UK to supply them to anyone under 18 if the supplier suspects they will be inhaled.",
        "description": "The deliberate inhalation of household products such as glue, aerosols, lighter fluid and solvents to produce a brief intoxicated state. Effects come on within seconds and last only a few minutes.",
        "risks": "Sudden Sniffing Death Syndrome — fatal heart failure that can occur on the very first use. Suffocation, choking on vomit, accidents while intoxicated. Long-term use damages the brain, liver, kidneys and heart.",
        "image": "images/volatile_substance_abuse.jpg",
        "image_credit": "https://en.wikipedia.org/wiki/Inhalant",
    },
}


# =============================================================
# generate popup HTML with embedded mini-chart
# Called by the map (Page 2)
# Uses matplotlib to render a small bar chart
def country_popup_html(country: str, count: int) -> str:
    subset = df[df["Country"] == country]

    age_counts = subset["Age"].value_counts().reindex(AGE_ORDER, fill_value=0)
    gender_counts = subset["Gender"].value_counts().reindex(["Male", "Female"], fill_value=0)

    fig, axes = plt.subplots(2, 1, figsize=(3.2, 2.6), dpi=110)

    # Age plot
    age_colors = [COLOR_MAPS["Age"].get(a, "#888") for a in age_counts.index]
    axes[0].barh(age_counts.index, age_counts.values, color=age_colors)
    axes[0].set_title("Age", fontsize=8)
    axes[0].invert_yaxis()  # 18-24 at the top
    axes[0].tick_params(labelsize=7)
    for spine in ("top", "right"):
        axes[0].spines[spine].set_visible(False)

    # Gender plot
    gender_colors = [COLOR_MAPS["Gender"].get(g, "#888") for g in gender_counts.index]
    axes[1].barh(gender_counts.index, gender_counts.values, color=gender_colors)
    axes[1].set_title("Gender", fontsize=8)
    axes[1].tick_params(labelsize=7)
    for spine in ("top", "right"):
        axes[1].spines[spine].set_visible(False)

    fig.tight_layout()

    # Encode the figure as base64 PNG for the popup
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    img_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    return (
        f"<div style='font-family: sans-serif; min-width: 260px;'>"
        f"<b style='font-size: 13px;'>{country}</b>"
        f"<div style='font-size: 11px; color: #666;'>{count} respondents</div>"
        f"<img src='data:image/png;base64,{img_b64}' "
        f"style='width: 100%; margin-top: 4px;'/>"
        f"</div>"
    )


# =============================================================
# SERVER
def server(input, output, session):

    # ---------------------------------------------------------
    # PAGE 2 — 'Show me' and 'Split by' in sync
    # user changes 'Show me', remove that variable from the 'Split by' choices so they cannot duplicate it.
    # ---------------------------------------------------------
    @reactive.effect
    def sync_demo_split():
        all_vars = ["Age", "Gender", "Education", "Country", "Ethnicity"]
        chosen = input.demo_show()

        # 'Country' as a Split-by is restricted to UK vs USA only
        choices = {"None": "none"}
        for v in all_vars:
            if v == chosen:
                continue
            if v == "Country":
                choices[v] = "Country (UK vs USA only)"
            else:
                choices[v] = v

        # If the current selection is no longer valid, reset to None
        current = input.demo_split()
        new_selected = current if current in choices else "None"

        ui.update_select("demo_split", choices=choices, selected=new_selected)

    # ---------------------------------------------------------
    # PAGE 2 — DEMOGRAPHIC PLOT
    # the same category always has the same colour across the app.
    # ---------------------------------------------------------
    @output
    @render_widget
    def demo_plot():
        var = input.demo_show()
        split = input.demo_split()

        data = df.copy()

        # If splitting by Country, restrict to UK + USA only
        if split == "Country":
            data = data[data["Country"].isin(["UK", "USA"])]

        if var == "Age":
            data[var] = pd.Categorical(data[var], categories=AGE_ORDER, ordered=True)
        elif var == "Education":
            data[var] = pd.Categorical(data[var], categories=EDUCATION_ORDER, ordered=True)

        if split == "None":
            counts = data[var].value_counts().sort_index()
            fig = px.bar(
                x=counts.index.astype(str),
                y=counts.values,
                color=counts.index.astype(str),
                color_discrete_map=COLOR_MAPS.get(var, {}),
                labels={"x": var, "y": "Number of respondents", "color": var},
            )
        else:
            grouped = data.groupby([var, split], observed=True).size().reset_index(name="count")
            fig = px.bar(
                grouped, x=var, y="count", color=split,
                barmode="group",
                color_discrete_map=COLOR_MAPS.get(split, {}),
                labels={"count": "Number of respondents"},
            )

        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        return fig

    # ---------------------------------------------------------
    # PAGE 2 — IPYLEAFLET MAP
    # Each marker has a popup containing a mini-chart (Age + Gender) rendered with matplotlib and embedded as a base64 PNG.
    # ---------------------------------------------------------
    @output
    @render_widget
    def demo_map():
        m = Map(
            center=(35.0, 0.0),
            zoom=2,
            basemap=basemap_to_tiles(basemaps.OpenStreetMap.Mapnik),
            scroll_wheel_zoom=True,
        )

        country_counts = df["Country"].value_counts()
        max_count = country_counts.max()

        for country, count in country_counts.items():
            coords = COUNTRY_COORDS.get(country)
            if coords is None:
                continue  # skip "Other" — no fixed location

            # Linear scale on sqrt-of-count → radius in pixels.
            radius = max(3, int((count / max_count) ** 0.5 * 30))

            #the popup HTML (header + embedded chart image)
            popup_html = HTML(country_popup_html(country, count))

            marker = CircleMarker(
                location=coords,
                radius=radius,
                color="#185FA5",
                fill_color="#378ADD",
                fill_opacity=0.6,
                weight=2,
            )
            marker.popup = popup_html
            m.add_layer(marker)

        return m

    # ---------------------------------------------------------
    # PAGE 3 — 'Drug' and 'Compare with' in sync
    # ---------------------------------------------------------
    @reactive.effect
    def sync_drug_compare():
        chosen = input.drug_pick()
        choices = {"None": "none"}
        for d in DRUG_COLS:
            if d != chosen:
                choices[d] = d

        current = input.drug_compare()
        new_selected = current if current in choices else "None"
        ui.update_select("drug_compare", choices=choices, selected=new_selected)

    # ---------------------------------------------------------
    # PAGE 3 — DRUG EXPLORER
    # ---------------------------------------------------------
    @reactive.calc
    def drug_data():
        breakdown = input.drug_breakdown()
        data = df.copy()

        if breakdown == "Country":
            data = data[data["Country"].isin(["UK", "USA"])]

        if breakdown == "Age":
            data["Age"] = pd.Categorical(data["Age"], categories=AGE_ORDER, ordered=True)
        elif breakdown == "Education":
            data["Education"] = pd.Categorical(data["Education"], categories=EDUCATION_ORDER, ordered=True)

        return data

    @output
    @render_widget
    def drug_freq_plot():
        drug = input.drug_pick()
        compare = input.drug_compare()

        # Reverse the freq order for horizontal display so "Never Used" is at the top and "Last Day" at the bottom (reads top-to-bottom).
        y_order = list(reversed(FREQ_ORDER))

        if compare == "None":
            counts = df[drug].value_counts().reindex(FREQ_ORDER, fill_value=0)
            fig = px.bar(
                x=counts.values, y=counts.index,
                orientation="h",
                labels={"x": "Number of respondents", "y": "Frequency of use"},
                title=f"How often respondents have used {drug}",
            )
        else:
            counts1 = df[drug].value_counts().reindex(FREQ_ORDER, fill_value=0)
            counts2 = df[compare].value_counts().reindex(FREQ_ORDER, fill_value=0)
            combined = pd.DataFrame({
                "Frequency": list(FREQ_ORDER) * 2,
                "Count": list(counts1.values) + list(counts2.values),
                "Drug": [drug] * len(FREQ_ORDER) + [compare] * len(FREQ_ORDER),
            })
            fig = px.bar(
                combined, x="Count", y="Frequency", color="Drug",
                orientation="h",
                barmode="group",
                title=f"{drug} vs {compare}",
            )

        fig.update_yaxes(categoryorder="array", categoryarray=y_order)
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        return fig

    @output
    @render_widget
    def drug_breakdown_plot():
        drug = input.drug_pick()
        compare = input.drug_compare()
        breakdown = input.drug_breakdown()
        apply_compare = input.apply_compare_breakdown()
        data = drug_data()

        active_set = {"Last Month", "Last Week", "Last Day"}

        if compare != "None" and apply_compare:
            # Show two drugs side-by-side per breakdown group
            rows = []
            for d in [drug, compare]:
                tmp = (
                    data.groupby(breakdown, observed=True)[d]
                        .apply(lambda s: s.isin(active_set).mean() * 100)
                        .reset_index(name="Active %")
                )
                tmp["Drug"] = d
                rows.append(tmp)
            result = pd.concat(rows, ignore_index=True)

            fig = px.bar(
                result, x="Active %", y=breakdown, color="Drug",
                orientation="h",
                barmode="group",
                title=f"% active users by {breakdown} — {drug} vs {compare}",
                labels={"Active %": "% Active users"},
            )
        else:
            result = (
                data.groupby(breakdown, observed=True)[drug]
                    .apply(lambda s: s.isin(active_set).mean() * 100)
                    .reset_index(name="Active %")
            )
            fig = px.bar(
                result, x="Active %", y=breakdown,
                orientation="h",
                title=f"% who used {drug} in the last month, by {breakdown}",
                labels={"Active %": "% Active users"},
            )

        # Reverse axis so the natural order reads top-to-bottom (e.g. youngest age group at the top)
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        return fig

    @output
    @render_widget
    def drug_summary_plot():
        drug = input.drug_pick()
        compare = input.drug_compare()
        apply_compare = input.apply_compare_summary()

        def make_row(d):
            active_pct = df[d].isin(["Last Month", "Last Week", "Last Day"]).mean() * 100
            never_pct = (df[d] == "Never Used").mean() * 100
            other_pct = 100 - active_pct - never_pct
            return active_pct, other_pct, never_pct

        if compare != "None" and apply_compare:
            rows = []
            for d in [drug, compare]:
                a, o, n = make_row(d)
                rows.append({"Drug": d, "Category": "Active (last month+)", "Percentage": a})
                rows.append({"Drug": d, "Category": "Used previously",     "Percentage": o})
                rows.append({"Drug": d, "Category": "Never used",          "Percentage": n})
            summary = pd.DataFrame(rows)

            fig = px.bar(
                summary, x="Percentage", y="Drug", color="Category",
                orientation="h",
                title=f"Usage profile — {drug} vs {compare}",
            )
        else:
            a, o, n = make_row(drug)
            summary = pd.DataFrame({
                "Category": ["Active (last month+)", "Used previously", "Never used"],
                "Percentage": [a, o, n],
            })
            fig = px.bar(
                summary, x="Percentage", y=[""] * 3, color="Category",
                orientation="h",
                text=summary["Percentage"].round(1).astype(str) + "%",
                title=f"Overall usage profile — {drug}",
            )

        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="% of respondents", yaxis_title="",
            barmode="stack",
        )
        return fig

    # ---------------------------------------------------------
    # PAGE 4 — PERSONALITY & DRUGS
    # ---------------------------------------------------------
    @output
    @render_widget
    def corr_heatmap():
        corr = pd.concat([df[PERSONALITY_COLS], df_drug_numeric], axis=1) \
                 .corr().loc[PERSONALITY_COLS, DRUG_COLS]

        fig = px.imshow(
            corr.round(2),
            color_continuous_scale="RdBu_r",
            color_continuous_midpoint=0,
            aspect="auto",
            text_auto=True,
            labels=dict(x="Drug", y="Personality trait", color="Correlation"),
        )
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        fig.update_xaxes(tickangle=45)
        return fig

    @output
    @render_widget
    def pers_drilldown():
        # Violin plot — shows distribution shape, median, IQR & outliers
        trait = input.pers_trait()
        drug = input.pers_drug()

        plot_df = pd.DataFrame({trait: df[trait], drug: df[drug]})
        plot_df[drug] = pd.Categorical(plot_df[drug], categories=FREQ_ORDER, ordered=True)
        plot_df = plot_df.sort_values(drug)

        fig = px.violin(
            plot_df, x=drug, y=trait,
            box=True,          
            points="outliers",  
            title=f"{trait} score by {drug} usage frequency",
            labels={trait: f"{trait} (standardised score)", drug: "Frequency of use"},
        )
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        return fig

    @output
    @render.ui
    def trait_glossary():
        # Show explanation for the currently selected personality trait
        trait = input.pers_trait()
        info = TRAIT_INFO.get(trait, {})

        return ui.div(
            ui.h4(trait),
            ui.p(
                ui.tags.small(
                    f"Part of the {info.get('model', '')}",
                    style="color: #888;",
                ),
            ),
            ui.p(ui.tags.b("What it measures: "), info.get("summary", "")),
            ui.layout_column_wrap(
                ui.div(
                    ui.h5("High score (above 0)"),
                    ui.p(info.get("high", "")),
                ),
                ui.div(
                    ui.h5("Low score (below 0)"),
                    ui.p(info.get("low", "")),
                ),
                width=1/2,
            ),
            ui.p(
                ui.tags.small(
                    "Scores are standardised — 0 is the average respondent. "
                    "+1 is roughly higher than 84% of respondents; -1 is lower than 84%.",
                    style="color: #888;",
                ),
            ),
        )

    # ---------------------------------------------------------
    # PAGE 5 — DRUG INFORMATION
    # ---------------------------------------------------------
    @output
    @render.text
    def info_title():
        return input.info_drug()

    @output
    @render.ui
    def info_content():
        drug = input.info_drug()
        info = DRUG_INFO.get(drug, {})

        # Image block — only shown if the file actually exists in /images
        image_block = ""
        img_path = info.get("image", "")
        if img_path and Path(img_path).exists():
            image_block = ui.div(
                ui.tags.img(
                    src=img_path,
                    style="max-width: 320px; max-height: 240px; border-radius: 6px;",
                ),
                ui.p(
                    ui.tags.small(info.get("image_credit", "") or "Image source: —"),
                    style="color: #888; margin-top: 4px;",
                ),
                style="margin-bottom: 1rem;",
            )

        return ui.div(
            image_block,
            ui.h4("Category"),
            ui.p(info.get("category", "") or "—"),
            ui.h4("Legal status"),
            ui.p(info.get("legal", "") or "—"),
            ui.h4("Description"),
            ui.p(info.get("description", "") or "—"),
            ui.h4("Risks"),
            ui.p(info.get("risks", "") or "—"),
        )


# =============================================================
# Build the app
# -------------------------------------------------------------
# We add a static asset route so the /images folder is served to the browser when image src="images/foo.jpg" is used.
# =============================================================
www_dir = Path(__file__).parent
static_assets = {"/images": www_dir / "images"} if (www_dir / "images").exists() else {}

app = App(app_ui, server, static_assets=static_assets)
