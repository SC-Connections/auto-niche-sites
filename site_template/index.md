---
layout: default
title: Home
---

# Welcome to {{NICHE_TITLE}}

This site features curated top 10 product lists for {{NICHE_TITLE}}.

## Latest Posts

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
      <span class="post-meta">{{ post.date | date: "%b %-d, %Y" }}</span>
    </li>
  {% endfor %}
</ul>

## How It Works

This site automatically fetches the latest product data from Amazon and creates curated top 10 lists. Each list is carefully selected to help you find the best products in this niche.

---

*As an Amazon Associate, we earn from qualifying purchases.*
