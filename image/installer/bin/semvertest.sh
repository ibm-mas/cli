
GITHUB_REF_NAME=10.0.0
GITHUB_REF_NAME=1.1.0


#SEMVER_XYZ="(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
#SEMVER_PRE="(-(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)(\.(0|[1-9][0-9]*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*)?"
#SEMVER_BUILD="(\+[0-9a-zA-Z-]+(\.[0-9a-zA-Z-]+)*)?"
#SEMVER_REGEXP="^${SEMVER_XYZ}${SEMVER_PRE}${SEMVER_BUILD}$"

  SEMVER_XYZ="(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
  SEMVER_PRE="(-(0|[1-9][0-9]*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(\.(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*)?"
  SEMVER_BUILD="(\+[0-9a-zA-Z-]+(\.[0-9a-zA-Z-]+)*)?"
  SEMVER_REGEXP="^${SEMVER_XYZ}${SEMVER_PRE}${SEMVER_BUILD}$"


if [[ ! $GITHUB_REF_NAME =~ $SEMVER_REGEXP ]]; then
  echo "Aborting release build.  Tag '$GITHUB_REF_NAME' does not match a valid semantic version string"
  exit 1
else
  echo "hi dave"
fi
