# Einführung

Die folgende Beschreibung soll ein Konzept für eine neue Version des OpenSlides
Servers vorstellen.


## Nur ein Server

Das Konzept geht in erster Linie davon aus, dass es nur einen einzigen
OpenSlides Server gibt. Es laufen daher nicht mehrere Prozesse parallel. Dies
vereinfacht das Locking. Der Nachteil ist jedoch, dass die Software nicht
skalliert. Sollte das ein Problem sein, kann das Konzept leicht erweitert
werden, dass mehrere OpenSlides Server parallel laufen können, in dem Fall muss
es ein zentrales Locking, zum Beispiel in einer redis-Datenbank geben.


## Programmiersprache

Da Konzept kann sowohl in Python als auch in Go umgesetzt werden.

Der Vorteil an Go liegt daran, dass es performanter ist. Insbesondere nutzt ein
Prozess alle Prozessorkerne. Dagegen nutzt eine Python-asyncio-Instanz nur einen
Kern. Gerade dann, wenn es nur einen Server geben soll, wird ein in Go
geschriebener Server deutlich mehr Clients verwalten können.

Der Vorteil an Python ist dagegen, dass es eine einfachere Sprache ist mit der
wir mehr Erfahrung haben. Es wird uns daher vermutlich leichter fallen, dass
Konzept in Python umzusetzen.


## Kein SQL

Die Daten werden nicht im SQL gespeichert sondern als `all_data` im Server
vorgehalten. Die Daten werden daher als ein großes Dict verwaltet. Welche
Datenbanksoftware zum Einsatz kommt ist letztendlich egal. Wenn es mehrere
Server geben soll, bietet sich redis an, da redis das locking sehr gut umsetzten
kann. Von mongodb möchte ich wegen der neuen Lizenz dringend abraten.


## Keine Required User

Eines der größten Probleme, die der aktuelle Server lösen muss ist, dass sich
die Daten gegenseitig referenzieren und der Client die referenzierten Dateien
auch dann sehen muss, wenn er eigentlich keine Rechte für diese Daten hat.

Dies ist insbesondere bei den required usern der Fall. Kommt jedoch auch an
anderen Stellen vor. Zum Beispiel bei der Agenda, die auf Topics, Motions und
Assigments verweist.

Im neuen Konzept soll dieses Problem dadurch gelöst werden, dass die von einem
Element benötigten Daten innerhalb des Elements mitgesendet werden. Zum Beispiel
für ein Motion:

```
{
  id: 5,
  title: Mehr Äpfel
  Submitter: {
    collection: users/user,
    id: 5,
    first_name: Max,
    last_name: Mustermann,
  },
}
```

Die Daten werden nur auf der Ebene der `restricted_data` eingebaut. Auf der
Ebene der `all_data` bleiben die Verweise so, wie sie schon jetzt sind.


# Daten lesen

Die Daten werden über websocket abgerufen. Eine rest-api gibt es nicht mehr. Für
debug-Zwecke kann der Client eine Ansicht anbieten, um die Daten übersichtlich
anzuzeigen.

Beim lesen ändert sich nichts vom aktuellen Konzept. Der Client fragt über die
websocket Verbindung entweder alle Daten oder alle Daten ab einer `change_id`
ab. Er erhält die Daten abhängig von seinen Rechten als `restricted_data`.


## referenced_data

Braucht ein Element um richtig angezeigt werden können andere Elemente, werden
diese in das Element mit eingebaut. Aus diesem Grund gibt es neben `full_data`,
`restricted_data` nun das weitere Format `referenced_data`. Jedes Element, dass
potenziell in ein anderes Element eingebunden wird kann dafür eine entsprechende
Funktion anbieten, welche die Daten entsprechend rendert. Gibt es diese Funktion
nicht, wird die Funktion `restrict_data()` mit dem anonymous user verwendet.

Der große Vorteil an dieser Art die Daten anzubieten besteht darin, dass beim
rendern eines User-Elements, wenn der aktuelle Nutzer nicht das Recht
`can_see_user` hat, nicht herausgefunden werden muss, ob dieses User-Element
trotzdem benötigt wird.


## RestrictedDataCache

Soweit es mehrere Server-Instanzen geben muss, sollte der Restricted_data_cache
wenn möglich abgeschafft werden. Aufgrund des `change_id`-Systems ist dieser
Cache eigentlich nicht mehr erforderlich. Der Nachteil an diesem Cache ist
jedoch, dass wenn ein User Daten nur lesen will, auch Daten in die Datenbank
geschrieben werden müssen. Bei diesem Schreiben braucht es ein Locking. Beim
aktuellen Server ist dies eine ganze menge an Logik, die man sich sparen könnte.


# Daten ändern

Das Konzept zum ändern von Daten ist von dem JS-Framework `redux` inspiriert.
Anstatt von typischen Rest-API-Funktionen wie create, update, patch und delete
auszugehen, werden die Daten durch `action`-Funktionen geändert.

Eine solche `action`-Funktion erwartet als Eingabewert ein `all_data`-Dict sowie
ein `payload`-Dict und gibt gibt als Rückgabewert ein neues `all_data`-Dict
zurück sowie eine Liste von Element-IDs, die sich geändert haben.

Alternativ könnte die Funktion auch `all_data` nicht als Rückgabewert
zurückgeben, sondern das übergebene `all_data` entsprechend verändern. Für
`redux` ist es sehr wichtig, dass die Übergebenen Daten nicht verändert werden.
Ob dies für uns erforderlich ist, kann ich noch nicht einschätzen. In Python ist
es relativ aufwendig eine Kopie eines dicts zu erstellen, daher wäre es deutlich
einfacher, dass übergebene Dict zu bearbeiten. Treten Fehler auf besteht dann
jedoch die Gefahr, dass korrupte Daten produziert werden.

Zu jeder `action` gibt es ein json-schema welches definiert, welches Format das
`payload` haben muss. Ist der Server in Go geschrieben, kann anstelle des
json-schemas auch ein entsprechender Type definiert werden.

Der Ablauf ist folgender:

1. Der Client nennt über http oder websocket den namen einer `action` und sendet
dazu einen entsprechenden `payload`.

1. Der Server überprüft den `payload` anhand des json-schemas oder dem Type.

1. Der Server sperrt `all_data`, so dass parallel kein anderer Schreibezugriff möglich ist.

1. Der vom Client übergebene `payload` wird bearbeitet. Es wird die aktuelle
Server-Zeit hinzugefügt sowie die User-ID des Nutzers, welcher die `action`
aufruft. Außerdem wird in das `payload` die change_id der aktuellen `all_data`
geschrieben.

1. Innerhalb der `action` werden zuerst die Permissions überprüft, daher anhand
der übergebenen `all_data` kontrolliert in welchen Gruppen der User ist und
welche Rechte er darüber hat.

1. Dann wird `all_data` verändert, bzw. eine neue Version erstellt.

1. Zuletzt wird der Lock auf `all_data` wieder gelöst.

Eine Action kann mehrere Elemente auf einmal bearbeiten. Zum Beispiel könnte es
eine user-multi-create `action` geben. Es könnte auch eine motion-import
`action` geben, welche nicht nur ein Motion anlegt, sondern auch alle hierfür
benötigten User.

Vermutlich wird jede App die typischen Rest-API-Funktionen als `action`
definierten, daher `actions` zum Anlegen, bearbeiten und löschen von Elementen.
Möglicherweise bietet es sich an hierfür generische `actions` anzubieten.

Gibt es mehrere Server-Instanzen muss der Lock in die Datenbank geschrieben
werden, damit alle Instanzen sich daran halten. Alternativ könnten die Daten
ohne einen Lock geschrieben werden und am Ende kontrolliert werden, ob eine
andere Instanz die Daten im selben Zeitpunkt verändert hat. Wenn ja wird die
Änderung nicht in die Datenbank geschrieben, sondern die `action` mit dem neuen
`all_data` erneut ausgeführt.


# Daten in Datenbank speichern

Nachdem eine `action` erfolgreich ausgeführt wurde, werden die Daten in die
Datenbank geschrieben.

Hierbei wird jedoch nicht `all_data` in die Datenbank geschrieben, sondern der
Name der `action` sowie der `payload`. Die Datenbank enthält daher nicht
unmittelbar eine Version von `all_data` sondern nur eine History von `payloads`
für `actions`, mit deren Hilfe `all_data` berechnet werden kann.

Auf diesen Weg enthält die Datenbank automatisch eine History. Fragt ein Client
eine alte Version der Datenbank an, muss `all_data` nur bis zu diesem Zeitpunkt
berechnet werden.

Aus jedem Eintrag in der Datenbank lässt sich eine change_id berechnen. Diese
besteht aus zwei Teilen. Der eine Teil ist der timestamp, der in jedem `payload`
enthalten ist. Der zweite Teil ist eine fortlaufende Nummer für Änderungen in
der selben Sekunde. Eine change_id sieht daher wie folgt aus (1546709183, 0).
Die beiden Zahlen können auch in einem anderen Format dargestellt werden, zum
Beispiel 1546709183-0.

Anders als bisher ist die change_id daher keine fortlaufende Zahl. Gibt es in
einer Sekunde keine Änderung, gibt es auch keine change_id mit dieser Änderung.
Da jedoch jeder `payload` die change_id der letzten Änderung enthält, kann
sichergestellt werden, dass keine Änderung in der Mitte fehlt.

Die eigentliche Datenbank besteht daher nur als den Änderungen. Daneben kann es
natürlich verschiedene Caches geben. Zum Beispiel einen `all_data` cache,
welcher die aktuellen `all_data` enthält.

Die allererste `action` geht davon aus, dass `all_data` ein leeres Dict ist.

Der Server bietet eine `create-all-data-action` an, welche als `payload` ein
`all_data` dict erhält und dieses als `all_data` zurückgibt. Hierdurch ist es
möglich alle alten Änderungen zu entfernen und durch ein
`create-all-data-action` zu ersetzen.


# Autoupdate

Wenn eine neue Änderung eingefügt wurde, werden die Clients hierüber informiert.

Gibt es nur eine Server-Instanz weiß diese automatisch von der Änderung Bescheid
und kann alle Client direkt informieren. Gibt es mehrere Server-Instanzen ist
jede Server-Instanz einmal mit der Datenbank verbunden und bekommt die Änderung
von der Datenbank gepusht. Zum Beispiel über einen [redis
stream](https://redis.io/topics/streams-intro).


## Geänderte Elemente

Da jede `action` die Elemente benennt, die es geändert hat, weiß der Server,
welche Elemente neu gerendert und verteilt werden müssen. Da referenzierte
Elemente in andere Elemente eingebaut werden, müssen zusätzlich die Elemente neu
gerendert werden, in welche ein Element eingebaut wurde. Wurde Beispielsweise
ein User geändert muss auch jedes Motion neu gerendert werden, welches diesen
User enthält.

Hierfür muss jedes Element, welches potenziell ein anderes Element referenziert
eine Funktion anbieten, welches für ein bestimmtes Element die Element-ids von
allen konkret refenzierten Elementen zurückgibt. Zum Beispiel gibt die Funktion
`motion.related_elements(motion_5)` die Element_ids der supporer und submitter
zurück.


## Cache für referenzierte Elemente

Damit diese Funktionen nicht permanent aufgerufen werden müssen wird ein Cache
angelegt in der Form `Dict[element_id, Set[element_id]]`, daher, es wird zu
jedem Element gespeichert, in welchen anderen Elementen es referenziert ist. Zum
Beispiel:

```
{
  'users/user:5': {'motions/motion:6', 'motions/motion:10'},
  'users/user:6': {'motions/motion:1', 'motions/motion:6'}',
  'topics/topic:1': {'agenda/item:1'},
}
```

Wird ein Element geändert, kann über diesen Cache sehr leicht herausgefunden
werden, welche weiteren Elemente ebenfalls neu gerendert werden müssen.

Dieser Cache muss immer dann aktualisiert werden, wenn ein Element sich
verändert. Wenn in dem Beispiel motions/motion:6 geändert wird, müssen die
entsprechenden Einträge gegebenenfalls angepasst werden. Wenn sich das nicht
effizient umsetzten lässt, könnte eine `action` Funktion als weiteren
Rückgabewert eine Liste von Element_ids zurückgeben, bei denen der Cache
aktualisiert werden muss. Zum Beispiel könnte die `add-supporter-action` die
Information zurückgeben, dass bei einem bestimmten User nun auf ein motion
referenziert.


## Nur nötige Daten ändern

Da nicht bei jeder Änderung eines Users sich die anderen Elemente tatsächlich
ändern, könnte die Rückgabe von `user.related_data(user_5)` mit der alten
ausgabe verglichen werden. Nur wenn diese Unterschiedlich ist, müssen die
anderen Elemente neu gerendert werden.


## Daten versenden

Nach dem die geänderten Elemente herausgefunden wurden, werden diese wie gehabt
an die Clients als restricted_data versandt. Hierbei wird den Clients die
aktuelle change_id sowie die letzte change_id mitgeteilt. Da die change_id nicht
mehr aufsteigend ist, kann der client anderenfalls nicht herausfinden, ob er ein
Paket verpasst hat.


# Projektor

# Authentifizierung

# Static files

# Media files

# Migrations

# Aufwandsabschätzung



# Probleme

* Permission ändenn sich
* Plugins
* Zeit syncronisation bei mehreren Servern
* Server-Code ändert sich. Wie kann `all_data` mit alten `actions` generiert werden.
