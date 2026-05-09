# Autoevoluce softwaru pomocí autonomních agentů řízených velkým jazykovým modelem

Tento repozitář obsahuje praktickou a experimentální část bakalářské práce zaměřené na autoevoluci softwaru za využití autonomních agentů řízených velkým jazykovým modelem. Repo slouží jako výzkumné zázemí pro návrh, spouštění a vyhodnocování experimentů, jejichž cílem je ověřit, do jaké míry je agentní systém schopen samostatně rozvíjet existující software na základě zadaných úloh.

V rámci experimentů jsou porovnávány různé architektury multiagentního řízení, různé způsoby formulace úloh a více výchozích aplikací. Repozitář proto neobsahuje pouze zdrojové kódy aplikací, ale také pomocné agenty, workflow definice, sady promptů a výsledková data potřebná pro reprodukovatelnost experimentu.

## Cíl repozitáře

Hlavním účelem tohoto repozitáře je:

- uchovávat výchozí verze zkoumaných aplikací,
- uchovávat experimentálně vzniklé evoluované varianty těchto aplikací,
- definovat promptovací strategie a agentní architektury použité při autoevoluci,
- automatizovat běh experimentů pomocí GitHub Actions,
- evidovat výsledky jednotlivých běhů ve strukturované podobě.

## Struktura repozitáře

### `.claude/`

Adresář `.claude/` obsahuje markdown soubory definující pomocné agenty používané při experimentální autoevoluci. Konkrétně se jedná o role analytik, programátor, tester, systémový architekt a návrhář UML artefaktů. Tyto soubory představují instrukční základ pro jednotlivé specializované agenty a vymezují jejich odpovědnosti v rámci víceagentního řešení.

Součástí adresáře jsou také konfigurační soubory prostředí, které upravují chování nástroje a jeho lokální nastavení.

### `.github/workflows/`

Adresář `.github/workflows/` obsahuje GitHub Actions workflow, která byla využita pro automatizované spouštění experimentů autoevoluce. Tyto workflow slouží zejména k:

- výběru konkrétní architektury multiagentního systému,
- výběru promptovací strategie,
- výběru výchozí aplikace,
- spuštění příslušné experimentální úlohy,
- orchestrace sdíleného běhu implementačního procesu.

V repozitáři se nachází zejména workflow `run_experiment.yml`, které slouží jako vstupní bod pro spuštění experimentu, a `claude-implement-shared.yml`, které definuje sdílenou logiku jednotlivých běhů. Tato část repozitáře byla využívána jako infrastrukturní vrstva pro automatizovanou autoevoluci zkoumaných aplikací.

### `baseline/`

Adresář `baseline/` obsahuje výchozí, tedy počáteční verze aplikací, od nichž experimentální autoevoluce vychází. Tyto aplikace reprezentují referenční stav před provedením jednotlivých evolučních kroků a slouží jako kontrolovaný vstup pro porovnání změn vzniklých činností agentního systému.

V aktuální podobě repozitáře se zde nacházejí tři základní aplikace:

- `calculator`
- `TODO`
- `github-workflow-manager`

Každá z těchto aplikací představuje samostatný základ, nad nímž jsou následně prováděny experimentální úlohy.

### `experiments/`

Adresář `experiments/` obsahuje výsledné varianty aplikací, které prošly procesem autoevoluce. Struktura odpovídá kombinaci:

- architektury multiagentního systému,
- strategie formulace zadání,
- konkrétní výchozí aplikace.

V repozitáři je tak uloženo celkem 27 experimentálních aplikací, což odpovídá kartézskému součinu:

- 3 architektury: `pipeline`, `broadcast`, `supervisor_as_tools`,
- 3 promptovací strategie: `user_stories`, `structured_text`, `test_driven`,
- 3 výchozí aplikace: `calculator`, `TODO`, `github-workflow-manager`.

Každá experimentální větev tedy reprezentuje jednu konkrétní konfiguraci autoevoluce. V rámci těchto adresářů se nachází nejen zdrojové kódy, ale často také testy, UML artefakty a další pomocné soubory vzniklé v průběhu experimentu.

### `prompts/strategies/`

Adresář `prompts/strategies/` obsahuje prompty použité v experimentální části práce. Tyto prompty jsou členěny podle zvolené strategie zadání úlohy a podle konkrétní aplikace. Každá strategie dále obsahuje sadu dílčích evolučních kroků.

V repozitáři jsou zastoupeny zejména následující strategie:

- `user_stories`
- `structured_text`
- `test_driven`

Pro každou kombinaci strategie a aplikace je připraveno deset navazujících úloh, například od přidání atributu doménové vrstvy přes rozšíření funkcionality až po architektonický refaktoring nebo doplnění GUI. Tato část repozitáře tedy reprezentuje experimentální zadání, které agenti v jednotlivých bězích řešili.

### `results/`

Adresář `results/` obsahuje výsledková data, zejména soubor `results.csv`, ve kterém jsou zaznamenány metriky dosažené v jednotlivých bězích experimentu. CSV soubor slouží jako podklad pro následné vyhodnocení v textu bakalářské práce.

Zaznamenané sloupce zahrnují například:

- použitou architekturu,
- zvolenou strategii,
- typ aplikace,
- číslo úlohy,
- Počet správných UML artefaktů
- Celkový počet UML artefaktů 
- skóre UML artefaktů, 
- úspěšnost kompilace,
- správnost provedených změn,
- Počet testů kolik prošlo
- Celkový počet testů
- úspěšnost testů,
- skóre statické analýzy,
- celkové skóre,
- dobu běhu,
- finanční náklady běhu.

Vybrané metriky je vhodné interpretovat následovně:

- `UML_score` vyjadřuje součet hodnocení UML artefaktů v daném běhu.
- `Total_UML_diagrams` udává celkový počet hodnocených UML diagramů.
- `Score_normalized` představuje normalizované UML skóre, kde maximální možná hodnota je `1`.
- `Tests_passing` udává počet úspěšně splněných testů.
- `Total_tests` udává celkový počet testů v daném běhu.
- `Tests_normalized` představuje normalizovanou úspěšnost testů, kde maximální možná hodnota je `1`.
- `Total_score` představuje agregované výsledné skóre běhu.

Při hodnocení jednotlivých UML artefaktů byla použita tříúrovňová škála:

- `0` znamená, že artefakt neodpovídá implementovanému systému,
- `0.5` znamená, že artefakt sice přibližně odpovídá systému, ale neodpovídá standardnímu UML zápisu,
- `1` znamená, že artefakt odpovídá systému i standardnímu UML zápisu.

Normalizace byla použita u UML skóre i u úspěšnosti testů tak, aby maximální dosažitelná hodnota obou metrik byla rovna `1`. Díky tomu jsou tyto ukazatele vzájemně lépe porovnatelné a mohou být přímo zahrnuty do agregovaného hodnocení.

Celkové skóre jednoho běhu je konstruováno jako součet dílčích metrik. Maximální možná hodnota `Total_score` je proto `7`, což odpovídá ideálnímu běhu, v němž jsou všechny sledované komponenty hodnocení splněny na maximální úrovni.

## Experimentální uspořádání

Repozitář je navržen tak, aby podporoval reprodukovatelné porovnání různých přístupů k autoevoluci softwaru. Každý experiment lze chápat jako kombinaci tří nezávislých proměnných:

1. architektura agentního systému,
2. forma zadání úlohy,
3. výchozí software, na němž je evoluce prováděna.

Nad touto strukturou jsou definovány jednotlivé evoluční kroky, které simulují postupný rozvoj aplikace v čase. Výsledkem je sada konzistentně organizovaných experimentálních artefaktů vhodných pro kvalitativní i kvantitativní vyhodnocení.

## Reprodukovatelnost a využití

Repozitář není zamýšlen pouze jako úložiště zdrojových kódů, ale jako kompletní experimentální základna bakalářské práce. Spojuje v sobě:

- vstupní aplikace,
- instrukce pro agenty,
- automatizační workflow,
- zadání experimentálních úloh,
- výstupy vzniklé autoevolucí,
- naměřené výsledky.

Díky této struktuře je možné zpětně dohledat, za jakých podmínek konkrétní experiment vznikl, jaké instrukce agent obdržel a jaké výsledky daný běh přinesl.
