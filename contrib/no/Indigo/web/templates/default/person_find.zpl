<span tal:define="title string:S�k etter personer;title_id string:person_find" tal:omit-tag=""><span metal:use-macro="tpl/macros/page">
<span metal:fill-slot="body" tal:omit-tag="">
<form action="#" method="get">
<input type="HIDDEN" name="action" value="do_person_find">

<dl>
  <!--TODO: update help slik at dette kan brukes-->
  <!--<dt><a tal:replace="structure python:help_link('person_find_filter', 'S�kefilter')"></a>-->
  <dt>S�kem�nster
  <dd><input type="TEXT" name="search_value" size="20">
  <br>
  <br>
  <dt>S�ketype
  <dd>
    <input type="RADIO" name="search_type" value="name" CHECKED>Navn <br>
    <input type="RADIO" name="search_type" value="uname">Brukernavn <br>
    <input type="RADIO" name="search_type" value="schoolname">Skolenavn <br>
    <input type="RADIO" name="search_type" value="date">F�dselsdato (����-MM-DD)
</dl>

<input type="SUBMIT" value="S�k"/>

</form>
</span></span></span>
