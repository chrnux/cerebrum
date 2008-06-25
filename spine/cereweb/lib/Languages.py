
class Languages(object):
    
    def __init__(self, lang):
        if lang == 'en':
            import activation_en as theLang
        elif lang == 'no':
            import activation_no as theLang
        else:
            import activation_en as theLang
        self.lang = theLang

    #
    # choose language
    #
    def get_choose_language_header_text(self):
        return self.lang.choose_language_header_text

    def get_choose_language_label_text(self):
        return self.lang.choose_language_label_text

    def get_choose_language_button_text(self):
        return self.lang.choose_language_button_text

    #
    # NIN page
    #
    def get_nin_header_text(self):
        return self.lang.nin_header_text

    def get_nin_body_text(self):
        return self.lang.nin_body_text

    def get_nin_submit_label_text(self):
        return self.lang.nin_submit_label_text

    def get_nin_submit_button_text(self):
        return self.lang.nin_submit_button_text

    def get_nin_not_legal_error_message(self):
        return self.lang.nin_not_legal_error_message

    #
    # Student identifaction number(SID) page
    #
    def get_sid_header_text(self):
        return self.lang.sid_header_text

    def get_sid_body_text(self):
        return self.lang.sid_body_text

    def get_sid_submit_label_text(self):
        return self.lang.sid_submit_label_text

    def get_sid_submit_button_text(self):
        return self.lang.sid_submit_button_text

    def get_sid_not_legal_error_mesage(self):
        return self.lang.sid_not_legal_error_mesage

    #
    # PIN-code page
    #
    def get_pin_header_text(self):
        return self.lang.pin_header_text

    def get_pin_body_text(self):
        return self.lang.pin_body_text

    def get_pin_submit_label_text(self):
        return self.lang.pin_submit_label_text

    def get_pin_submit_button_text(self):
        return self.lang.pin_submit_button_text

    def get_pin_help_text(self):
        return self.lang.pin_help_text

    def get_pin_not_legal_error_message(self):
        return self.lang.pin_not_legal_error_message

    #
    # end user license agreement (eula)
    #
    def get_eula_header_text(self):
        return self.lang.eula_header_text

    def get_eula_bokmaal_link(self):
        return self.lang.eula_bokmaal_link

    def get_eula_english_link(self):
        return self.lang.eula_english_link

    def get_eula_bokmaal_link_text(self):
        return self.lang.eula_bokmaal_link_text

    def get_eula_english_link_text(self):
        return self.lang.eula_english_link_text

    def get_eula_legal_notes_text(self):
        return self.lang.eula_legal_notes_text

    def get_eula_accept_label_text(self):
        return self.lang.eula_accept_label_text

    def get_eula_accept_button_text(self):
        return self.lang.eula_accept_button_text

    #
    # set password
    #
    def get_setpassword_header_text(self):
        return self.lang.setpassword_header_text

    def get_setpassword_username_text(self):
        return self.lang.setpassword_username_text

    def get_setpassword_choose_self_text(self):
        return self.lang.setpassword_choose_self_text

    def get_setpassword_choose_generated_text(self):
        return self.lang.setpassword_choose_generated_text

    def get_setpassword_password_label1_text(self):
        return self.lang.setpassword_password_label1_text

    def get_setpassword_password_label2_text(self):
        return self.lang.setpassword_password_label2_text

    def get_setpassword_warning_text(self):
        return self.lang.setpassword_warning_text

    def get_setpassword_submit_button_text(self):
        return self.lang.setpassword_submit_button_text

    def get_setpassword_legal_passwords_text(self):
        return self.lang.setpassword_legal_passwords_text

    def get_setpassword_too_short_error_message(self):
        return self.lang.setpassword_too_short_error_message

    def get_setpassword_no_match_error_message(self):
        return self.lang.setpassword_no_match_error_message

    #
    # end page
    #
    def get_congratulations_header_text(self):
        return self.lang.congratulations_header_text

    def get_congratulations_body_text(self):
        return self.lang.congratulations_body_text
    #
    # eula not approved page
    #
    def get_eula_not_approved_header_text(self):
        return self.lang.eula_not_approved_header_text

    def get_eula_not_approved_body_text(self):
        return self.lang.eula_not_approved_body_text

    #
    # username not found page.
    #
    def get_username_not_found_header_text(self):
        return self.lang.username_not_found_header_text

    def get_username_not_found_body_text(self):
        return self.lang.username_not_found_body_text

    #
    # error in input data page.
    #
    def get_error_in_input_header_text(self):
        return self.lang.error_in_input_header_text

    def get_error_in_input_body_text(self):
        return self.lang.error_in_input_body_text

