==============
Overview
==============
.. Quick intro to what Cerebrum is and can do for your organisation.
   Currently only in Norwegian.

   TODO: Dette er cut&paste fra www.cerebrum.usit.uio.no, og litt
   selger preget?

Hva gir Cerebrum
-----------------
Cerebrum gir institusjonens systemer og applikasjoner ett sentralt sted
� hente ut og legge inn brukerdata. Det gir en mulighet til � bygge,
endre og slette brukere p� ett sted, og spre det til andre systemer.
Typiske eksempler p� bruk av Cerebrum er: tildeling av rettigheter,
printerkvoter og gruppemedlemskap.

Cerebrum vil med utgangspunkt i data fra din institusjons autoritative
administrative systemer kunne bidra til en automatisering av
brukeradministrasjonen av s�vel student- som ansattbrukere.

Ved etablering av nye systemer vil man kunne velge import fra Cerebrum i
henhold til anerkjente internasjonale standarder, eller skreddersy en
import ut fra et rikt API-sett.


Hva er Cerebrum
----------------
Cerebrum er et brukeradministrativt system (BAS), utviklet ved
Universitetets senter for informasjonsteknologi (USIT) ved Universitetet
i Oslo (UiO). Cerebrum er utviklet i samsvar med de krav satt til et BAS
i FEIDE, og med st�tte fra FEIDE-prosjektet. Cerebrum gir dine brukere
mulighet til � ha ett brukernavn og ett passord som kan brukes i alle
institusjonens systemer. Ved deltagelse i FEIDE f�r de samtidig tilgang
til et spekter av sektorvise fellestjenester.

Cerebrum er i dag en Python/RDBMS-basert �verkt�ykasse� med st�tte for
PostgreSQL. Det foreligger en enkel kommandolinjebasert
administrasjonsklient, skrevet i Java. Ved Norges
teknisk-naturvitenskapelige universitet (NTNU) utvikles det med st�tte
fra FEIDE-prosjektet en administrasjonsklient med et grafisk
brukergrensesnitt. Dette er et ledd i NTNUs etablering av Cerebrum.

Cerebrum best�r av en kjerne som definerer de sentrale tabellene og
entitetene, og som gir et API mot disse. Cerebrum har i tillegg et
st�rre sett med moduler som muliggj�r integrasjon mot omkringliggende
systemer. Per i dag finnes det moduler for:


* Felles Studentsystem (FS)
* L�nns- og Trekksystem (LT)
* SAP
* ActiveDirectory
* Novell
* NIS
* LDAP
* MAIL-modul
* ClassFronter



Hvordan ta i bruk Cerebrum
---------------------------
Systemet er i dag i full produksjon ved UiO og er grunnsteinen i den
daglige administreringen av alle brukerne, b�de studenter og ansatte.
Cerebrum tilbys gjennom flere alternative varianter.

1. �Do It Yourself� . Cerebrum som GPL Open Source, fritt nedlastbar fra
   http://cerebrum.sf.net, men det f�lger ingen support med systemet
2. �Support�. Cerebrum med support fra USIT
3. �ASP�. USIT gir support og drifter Cerebrum for institusjonen

Ved � velge alternativ 2 eller 3 vil man betale en pris per bruker, samt
at man f�r support og oppdateringer fra USIT. I tillegg vil man f�
mulighet til � delta p� et �rlig Cerebrum brukerforum. Vi tilbyr
r�dgivningstjenester og konsulentvirksomhet for � tilpasse Cerebrum til
alle institusjoner i sektoren. For pris, ta kontakt med USIT.


Hovedpunkter


* Samme brukernavn og passord for alle tjenester
* Ett sted � oppdatere informasjon om brukere, uansett hvilket
  system/OS brukeren benytter
* Ett synkroniseringspunkt for informasjon om personer
* Ett kontaktpunkt for eksterne personer som �nsker autentiserings- og
  autorisasjonsinformasjon
* Ett utgangspunkt for levering av informasjon til nye tjenester

..
