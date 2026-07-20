class Standing {
  final String teamId;
  int position     = 0;
  int points       = 0;
  int played       = 0;
  int won          = 0;
  int drawn        = 0;
  int lost         = 0;
  int goalsFor     = 0;
  int goalsAgainst = 0;

  Standing(this.teamId, {int pointDeduction = 0}) {
    points -= pointDeduction;
  }

  int get goalDiff => goalsFor - goalsAgainst;
}
