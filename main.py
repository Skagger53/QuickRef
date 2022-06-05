# Quick Ref copyright 2022
# Quick Ref is software by Matt Skaggs to expedite BOM referral financial reviews at a SNF healthcare facility by generating email responses.
# Redistribution of this code without the author's explicit permission is prohibited.

if __name__ != "__main__":
    print("This is a standalone module. Run directly.")
else:
    import os
    import pyperclip

    # Checks if user's input is in a provided range.
    # accepted is a list of consecutive number options to choose.
    # Returns 0 = No, 1 = Yes.
    # Called from payer_setup(), get_ma_type().
    def input_validation_list(user_input, accepted):
        if user_input in accepted: return 1
        print(f"Please enter a number from 1 to {accepted[-1]}.")
        return 0

    # Checks if user's input is an integer or not.
    # Returns integer version of input if yes. If no, returns None.
    # Called from payer_setup(), get_ma_type().
    def payer_setup_type_validation(user_input, accepted):
        try:
            user_input = int(user_input)
            return int(user_input)
        except ValueError:
            print(f"Please enter a number from 1 to {accepted[-1]}.")
            return None

    # Asks user to select a payer. Process is the the same for primary and secondary, so this function is used for both.
    # Returns the user's selection if input is validated; invalid input returns None.
    # options is consecutively numbered dictionary of payers that starts at 1.
    # Called from get_ma_type(), payers_input().
    def payer_setup(directions, options, prim_payer_input = None):
        print(directions)
        for option in range(1, len(options) + 1): print(f"{option}: {options[option]}")
        prim_payer_input = payer_setup_type_validation(input(), list(options.keys())) # payer_setup_type_validation checks that the user entered an integer.
        if prim_payer_input == None: return None
        if input_validation_list(prim_payer_input, list(options.keys())) == 1: return prim_payer_input # input_validation_list returns 1 if input is integer from range, 0 if not.
        return None

    # Getting the MA type.
    # None is returned to indicate an error from user input.
    # Called from payers_input().
    def get_ma_type(ma_types):
        ma_type_list_len = range(1, len(ma_types) + 1 )
        print("What type of MA?")
        for ma_type_options in ma_type_list_len: print(f"{ma_type_options}: {ma_types[ma_type_options]}")
        ma_type = payer_setup_type_validation(input(), ma_type_list_len) # payer_setup_type_validation checks that the user entered an integer.
        if input_validation_list(ma_type, ma_type_list_len) == 1: return ma_type # input_validation_list returns 1 if input is integer from range, 0 if not.
        return None

    # Asking user for input for payers.
    # Payer always starts as None, setup_options is the questions asked of the user, and validation_list is the integers that will be accepted.
    # Called from payers_setup().
    def payers_input(directions, payer, setup_options, managing_payers, ma_types):
        managing_payer = None
        while payer == None: payer = payer_setup(directions, setup_options, setup_options)

        if payer == 2 or payer == 4 or payer == 5: # If payer is managed (or MSHO for primary)
            managing_payer = None # None is used to indicate user input error for payer_setup().
            while managing_payer == None: managing_payer = payer_setup("Who is managing?", managing_payers)

        # This is to obtain MA type if the user has selected MA/Managed MA.
        ma_type = None
        if "MA" in setup_options[payer]:
            while ma_type == None: ma_type = get_ma_type(ma_types)
        return payer, managing_payer, ma_type

    # Creating email text based on all possible combinations of payers.
    # User input errors from incompatibilities return None. Called from main().
    def output_text(prim_payer, prim_man_payer, sec_payer, sec_man_payer, managing_payers, ma_types, ma_type):
        # Catching incompatible user selections.
        
	# MSHO MA type selected but MSHO wasn't selected as primary payer AND primary or secondary managing payers are not selected.
	# Choosing MA type MA02 is acceptable ONLY if identical primary/secondary managing insurances were previously selected.
	if ma_type == 1 and (prim_payer != 5 and (prim_man_payer == None or sec_man_payer == None)):
            print("\nIncompatible setup (MSHO requires identical Medicare and Medicaid managing insurances). Please start over.")
            return None
        
	# If MA02 is selected but different primary/secondary managing insurances were selected.
	if ma_type == 1 and (managing_payers[prim_man_payer] != managing_payers[sec_man_payer]):
            print("\nIncompatible setup (different managing Medicare and managing Medicaid insurances, yet MA type is MA02 MSHO). Please start over.")
            return None
        
	# If MA12 was selected but primary payer is anything other than straight MA.
	if ma_type == 2 and prim_payer != 3:
            print("\nIncompatible setup (MA12 type can only be straight MA). Please start over.")
            return None
		
	# Returning email text
		
	# MSHO type selected when primary/secondary managed payers are identical.
	if ma_type == 1: return f"\nFronts are fine. MSHO with {managing_payers[prim_man_payer]}."

	# Checking all possible acceptable user input combinations.
        ma_types[7] = "none/unspecified" # Changing the initial capital to lowercase
        match prim_payer:
            case 1: # Primary Medicare
                match sec_payer:
                    case 1: # Primary Medicare, secondary MA
                        return f"Fronts are fine. Skilled is Medicare. Non-skilled is MA ({ma_types[ma_type]})."
                    case 2: # Primary Medicare, secondary managed MA
                        return f"Fronts are fine. Skilled is Medicare. Non-skilled is MA ({ma_types[ma_type]}) managed by {managing_payers[sec_man_payer]}."
                    case 3: # Primary Medicare, secondary PP
                        return f"Fronts are not OK. Skilled is Medicare. No non-skilled payer.\n\nUnless the patient wants to be PP for copays (and/or full payments if Medicare ends), I'll need one of two things to accept:\n1. A completed MA application for me to review.\n2. The patient's stated DC plan if they want to avoid SNF day 21+ daily copays ($194.50) and/or full private pay if Medicare coverage ends."
            
			case 2: # Primary managed Medicare
                match sec_payer:
                    case 1: # Managed Medicare, secondary straight MA
                        return f"Fronts are fine. Skilled is Medicare managed by {managing_payers[prim_man_payer]}. Non-skilled is straight MA ({ma_types[ma_type]})."
                    case 2: # Managed Medicare, secondary Managed MA
                        return f"Fronts are fine. Skilled is Medicare managed by {managing_payers[prim_man_payer]}. Non-skilled is MA ({ma_types[ma_type]}) managed by {managing_payers[sec_man_payer]}."
                    case 3: # Managed Medicare, secondary PP
                        return f"Fronts are not OK. Skilled is Medicare managed by {managing_payers[prim_man_payer]}. No non-skilled payer.\n\nUnless the patient wants to be PP for copays (and/or full payments if Medicare ends), I'll need one of two things to accept:\n1. A completed MA application for me to review.\n2. The patient's stated DC plan if they want to avoid SNF day 21+ daily copays ($194.50) and/or full private pay if Medicare coverage ends."
            
			case 3: # Primary straight MA
                return f"Fronts are fine. No skilled payer. Non-skilled is straight MA ({ma_types[ma_type]})."
            
			case 4: # Primary managed MA
                return f"Fronts are fine. No skilled payer. Non-skilled is MA managed by {managing_payers[prim_man_payer]} ({ma_types[ma_type]})."
            
			case 5:  # Primary MSHO
                return f"Fronts are fine. MSHO with {managing_payers[prim_man_payer]} (MA02 MSHO)."
            
			case 6: # Primary PP
                return "Only payer is private pay.\n\nWe will require a down payment of $3500 to accept. I also need to know the patient's stated plans for either DC or contnuation of payment after the $3500 is exhausted, which will be approximately 8 or 9 days (and could be less)."

    # Getting all payers from user. Called from main()
    def payers_setup(prim_payers_list, sec_payers_list, managing_payers, ma_types):
        prim_payer, prim_man_payer, ma_type = payers_input("Who is the primary payer?", None, prim_payers_list, managing_payers, ma_types)
        os.system("cls")

        # Isolating cases where secondary payer does not need to be obtained.
        match prim_payer:
            case 3 | 4: return prim_payer, prim_man_payer, None, None, ma_type # MA or managed MA. Returns RR automatically.
            case 5: return prim_payer, prim_man_payer, 2, prim_man_payer, 1 # MSHO. Returns managed MA and identical primary/secondary managing insurances.
            case 6: return prim_payer, prim_man_payer, None, None, None # PP

        # Inquiring from the user what the secondary payer is.
        sec_payer, sec_man_payer, ma_type = payers_input("Who is the secondary payer?", None, sec_payers_list, managing_payers, ma_types)
        return prim_payer, prim_man_payer, sec_payer, sec_man_payer, ma_type

    def main():
        # Master lists.
        prim_payers_list = {1: "Medicare", 2: "Managed Medicare", 3: "MA", 4: "Managed MA", 5: "MSHO", 6: "Private pay"}  # These are hard-coded. Making a change here will require changing the match-case in output_text().
        sec_payers_list = {1: "MA", 2: "Managed MA", 3: "Private pay"}  # These are hard-coded. Making a change here will require changing the match-case in output_text().
        managing_payers = {1: "Aetna", 2: "Cigna", 3: "BCBS", 4: "Humana", 5: "Medica", 6: "UHC", 7: "HealthPartners", 8: "UCare"} # This dictionary can be altered without issue as long as the numbering system is consecutive and starts at 1.
        ma_types = {1: "MA02 MSHO", 2: "MA12 PMAP", 3: "MA17 SNBC", 4: "MA25 MSC+", 5: "MA30 MSC+", 6: "MA35 MSC+", 7: "None/unspecified"} # NOTE: Key 7 is hard-coded in output_text() to change the value to be in all lowercase. To change this list, ensure that the case change in output_text() references the correct key for value "None/unspecified". Aside from that, this dictionary may be changed as long as the numbers begin at 1 and are consecutive.

        # This begins user interaction. Obtains all payer information. Arguments are master payer lists.
        prim_payer, prim_man_payer, sec_payer, sec_man_payer, ma_type = payers_setup(prim_payers_list, sec_payers_list, managing_payers, ma_types)

        # This obtains and displays the final email message output
        os.system("cls")
        output = output_text(prim_payer, prim_man_payer, sec_payer, sec_man_payer, managing_payers, ma_types, ma_type)
        if output != None: # Any incompatible input will always return None for output variable
            print(output)
            pyperclip.copy(output)
            print("\n----------------\n\nThe above message has been copied to your clipboard.\n")

    main()
