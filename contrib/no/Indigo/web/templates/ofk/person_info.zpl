<span tal:define="title string:Personinformasjon;title_id string:person_info" 
      tal:omit-tag="">
  <span metal:use-macro="tpl/macros/page">
    <span metal:fill-slot="body" tal:omit-tag="">

      <br>
      <hr>

      <table border=1>
	<tr>
	  <td>Navn</td> 
	  <td tal:content="person/name">En Person</td>
	</tr>

        <tr>
	  <td valign="top">Tilgjengelige tjenester:</td> 
	  <td>
	    <span tal:repeat="pspread person_spreads" tal:omit-tag="">
              <span tal:content="string:${pspread/spread_desc}"></span>

	      <br>
            </span>
	  </td>
        </tr>	 

        <tr>
          <td>F�dselsdato</td>
	  <td tal:content="person/birth">1999-99-99</td>
        </tr>
        <tr>
          <td>F�dselsnummer</td>
	  <td tal:content="person/fnrs">fnr</td>
        </tr>

        <tr>
          <td>Tilknytning</td>
          <td>
            <span tal:repeat="aff affiliations" tal:omit-tag="">
              <span tal:content="string:${aff}"></span>
              <br>
            </span>
          </td>
        </tr>
      </table>

      <br>
      <hr>
      <h1>Brukerinformasjon</h1>

      <table border="0" tal:repeat="user userlist">
        <tr>
	  <td>Brukernavn:</td> 
	  <td tal:content="user/username">foo</td>
	</tr>

        <tr>
	  <td valign="top">Gruppemedlemskap:</td> 
	  <td> 
	    <span tal:repeat="ugroup user/groups" tal:omit-tag="">
	      <span tal:content="ugroup/group"></span>
 
              <br>
            </span>
          </td>
        </tr>

        <tr>
	  <td valign="top">Prim�r e-postadresse:</td> 
	  <td tal:content="user/email">addresse</td>
        </tr>

        <tr tal:condition="user/email_addresses">
	  <td valign="top">E-postalias:</td> 
	  <td> 
        <form method="post" action="#">
        <input type="hidden" name="action" value="do_email_remove_address">
        <input type="hidden" name="username" tal:attributes="value string:${user/username}">
        <table>

	    <span tal:repeat="address user/email_addresses" tal:omit-tag="">
            <tr>
                <td><input type="checkbox" name="address" tal:attributes="value string:${address}"></td>
                <td><span tal:content="address"></span></td>
            </tr>
        </span>
        <tr>
            <td></td>
            <td><input type="submit" name="do_email_remove_address" value="Slett alias"></td>
        </tr>
        </table>
        </form>
      </td>
    </tr>

    <tr>
	  <td colspan=2></td>
	</tr>

	<tr>
	  <td colspan=2></td>
        </tr>

        <span tal:condition="python: state['authlevel'] > 'c1'" tal:omit-tag="">
          <tr> 
	    <td colspan=2>
	      <a tal:attributes="href string:?action=do_user_password&entity_id=${user/account_id}">Sett nytt passord (automatisk generert)</a>
            </td>
          </tr>
          <tr>
            <td colspan=2>
              <a tal:attributes="href string:?action=show_user_get_password&entity_id=${user/account_id}">Hent ut brukerens n�v�rende passord</a>
            </td>
          </tr>
          <tr>
	    <td colspan=2> </td>
          </tr>
        </span>
      <span tal:condition="python: state['authlevel'] > 'c2'" tal:omit-tag="">
        <tr>
          <td colspan=2>
            <a tal:attributes="href string:?action=show_email_add_address&username=${user/username}">Opprett nytt e-post alias for denne brukeren</a>
          </td>
        </tr>
        <tr>
          <td colspan=2>
            <a tal:attributes="href string:?action=show_user_create&owner_id=${person/entity_id}&owner_type=person">Opprett ny bruker til denne personen</a>
          </td>
        </tr>
      </span>
      </table>  <!-- brukerinformasjon -->
 
      <br>
      <hr>

      <h1>Endre prim�r e-postadresse</h1>

      <span tal:condition="python: state['authlevel'] > 'c1'" tal:omit-tag="">
        <span tal:condition="user_priorities" tal:omit-tag="">
          <table border="1">
            <tr>
              <td>Prioritet</td>
              <td>Bruker</td>
              <td>Tilknytning</td>
            </tr>

            <tr tal:repeat="upri user_priorities">
              <td><a tal:content="upri/priority"
                     tal:attributes="href string:?action=do_user_priority_mod&owner_id=${person/entity_id}&from_priority=${upri/priority}"></a>
              </td>
              <td tal:content="upri/uname">brukernavn</td>
              <td tal:content="upri/affiliation">giske skole</td>
            </tr>
          </table>
        </span>
      </span>

    </span>
  </span>
</span>

