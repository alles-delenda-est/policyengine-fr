# Upstream proposal — offer `policyengine-fr` to the PolicyEngine org (STRATEGY.md S1)

Outreach to ask whether France should become a PolicyEngine country package.
This prepares S1; it does not make the S1 decision — dispatch when you've decided
to reach out. The message body is in [`upstream-proposal-body.md`](upstream-proposal-body.md).

## Dispatch (via `gh`)

Open it as an issue on the PolicyEngine mono-repo:

```sh
gh issue create \
  --repo PolicyEngine/policyengine \
  --title "France country package proposal (built on policyengine-core)" \
  --body-file docs/upstream-proposal-body.md
```

To open a Discussion instead (no direct `gh` sub-command — use the API):

```sh
# category id from: gh api graphql -f query='{repository(owner:"PolicyEngine",name:"policyengine"){discussionCategories(first:20){nodes{id name}}}}'
gh api graphql -f query='mutation($repo:ID!,$cat:ID!,$title:String!,$body:String!){createDiscussion(input:{repositoryId:$repo,categoryId:$cat,title:$title,body:$body}){discussion{url}}}' \
  -f repo="$(gh api repos/PolicyEngine/policyengine --jq .node_id)" \
  -f cat="<category-id>" \
  -f title="France country package proposal (built on policyengine-core)" \
  -f body="$(cat docs/upstream-proposal-body.md)"
```

Then drop the resulting link in the PolicyEngine Slack.

## Before dispatching

The PyPI-name question (point 2) is worth acting on regardless of the reply:
claiming `policyengine-fr` on PyPI now — even an empty placeholder — removes the
squat risk. Do that independently of waiting for an answer.
