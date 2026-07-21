# Agent Skills

Здесь лежат десять моих Agent Skills для Claude Code и Codex. Я пользуюсь этими же файлами сам: глобальные скиллы на моём компьютере подключены к репозиторию через symlink. Поэтому обновления не расходятся с рабочей версией.

Префикс `x9-` нужен, чтобы мои скиллы не конфликтовали с одноимёнными пакетами и локальными навыками в других проектах.

## Что внутри

- `x9-agent-instructions` - глобальные правила агентов и разовые брифы
- `x9-browser-session` - работа с локальным и залогиненным браузером без потери сессии
- `x9-codex-delegation` - делегирование задач из Claude Code в Codex
- `x9-context-files-generator` - создание и обновление `AGENTS.md`, `CLAUDE.md` и README
- `x9-idea-critic` - критика идеи несколькими независимыми маршрутами
- `x9-loop-engineering` - проектирование ограниченных автономных циклов
- `x9-okf-adapt` - перенос Markdown-баз знаний в OKF v0.1
- `x9-research` - ресерч по актуальным источникам
- `x9-skill-creator` - создание, аудит и доработка Agent Skills
- `x9-wb-product-search` - поиск товаров на Wildberries с проверкой вариантов и отзывов

## Установка

Посмотреть список:

```bash
npx skills add xonika9/agent-skills --list
```

Установить один скилл глобально:

```bash
npx skills add xonika9/agent-skills --skill x9-research -g -y
```

Установить все:

```bash
npx skills add xonika9/agent-skills --all -g
```

Репозиторий использует стандартную структуру `skills/<name>/SKILL.md`, которую понимает CLI [`skills`](https://github.com/vercel-labs/skills).

## Залогиненный браузер

`x9-browser-session` описывает мою рабочую схему: отдельный профиль Microsoft Edge, локальный CDP на порту `9222`, `chrome-devtools` как основной контроллер и `agent-edge` как запасной. Инструкция по установке лежит в [skills/x9-browser-session/references/setup.md](skills/x9-browser-session/references/setup.md).

Профиль браузера, cookies и авторизационные данные в репозиторий не входят.

## Глобальные правила

Корневые `AGENTS.md` и `CLAUDE.md` содержат один и тот же `SHARED PERSONAL CORE`: язык, границы полномочий, сохранение пользовательских изменений и проверяемый критерий готовности. Полные глобальные инструкции моего компьютера в репозиторий не входят.

## Проверка

Проверить структуру всех скиллов:

```bash
for skill in skills/*; do
  python3 skills/x9-skill-creator/scripts/validate.py "$skill"
done
```

Проверить локальное обнаружение:

```bash
npx skills add . --list
```

Структурная проверка не доказывает поведение модели. Для изменений, от которых зависит рабочий маршрут, нужны отдельные живые тесты в Claude Code и Codex.
