<span tal:define="title string:Brukere;title_id string:user_find_res" tal:omit-tag=""><span metal:use-macro="tpl/macros/page">
<span metal:fill-slot="body" tal:omit-tag="">
<!--Forel�pig ikke i bruk-->
<span tal:condition="not:userlist" tal:omit-tag="">
 Ingen brukere oppfylte dine s�kekriterier.
</span>

<span tal:condition="userlist" tal:omit-tag="">
Klikk p� brukernavn for � velge bruker.

  <table border="1">
    <tr><th>Brukernavn</th> <th>Sluttdato</th> <th>Prim�r tilknytning</th> <th>Brukergruppe</th></tr>
    <tr valign="top" tal:repeat="user userlist"
        tal:attributes="class python:test(path('repeat/user/odd'), 'white', 'grey')">
      <td><a tal:attributes="href string:?action=do_select_target&type=account&entity_id=${user/entity_id}" tal:content="user/username">foo\
user</a></td>
      <td tal:content="user/expire">2001-01-02</td>
      <td>Student ved Matnant (150000)</td>
      <td>hjemmeomr�de bruker</td> <!-- ldap, mail, windows, hjemmeomr�de -->
    </tr>
  </table>
</span>

</span></span></span>
