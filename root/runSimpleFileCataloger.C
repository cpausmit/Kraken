#if !defined(__CLING__) || defined(__ROOTCLING__)
#include <TROOT.h>
#include <TH1F.h>
#include <TSystem.h>
#endif

const TString slash      = "/";
const TString hadoopDoor = "root://xrootd.cmsaf.mit.edu/";

void catalogFile(const char *dir, const char *file);
void reset();

//--------------------------------------------------------------------------------------------------
void runSimpleFileCataloger(const char *dir  = "/tmp",
			    const char *file = "SIDIS+pythia6+ep_18x100+run001+1900000_10000_tmp.root")
{
  // -----------------------------------------------------------------------------------------------
  // This script runs a full cataloging action on the given directory/file combination
  // -----------------------------------------------------------------------------------------------

  if (strcmp(file,"") == 0) {
    string s;
    ifstream infile;
    cout << " Open file" << endl;
    infile.open("tmp_list.txt");
    while (! infile.eof()) {
      getline(infile,s);
      if (s.length() == 0)
	continue;

      cout << "String found: " << s << endl;

      // find the filename only
      string tmp = s;
      //string d = "/mnt/hadoop";
      string d = "";
      string delimiter = "/";
      size_t pos = 0;
      size_t lpos = 0;
      string token;
      while ((pos = tmp.find(delimiter)) != std::string::npos) {
	if (pos != 0)
	  d += delimiter + tmp.substr(0, pos);
	tmp.erase(0,pos+delimiter.length());
      }
      cout << "  Dir: " << d << endl;
      cout << " File: " << tmp << endl;
      catalogFile(d.data(),tmp.data());
    }
    infile.close();
    reset();
  }
  else {
    reset();
    catalogFile(dir,file);
  }
  return;
}

//--------------------------------------------------------------------------------------------------
void catalogFile(const char *dir, const char *file)
{
  TString fileName = TString(dir) + slash +  + TString(file);
  //if      (fileName.Index("SUEP") != -1) {
  //  printf("Leave name unchanged: %s\n",fileName.Data());
  //}
  if (fileName.Index("/mnt/hadoop/cms/store") != -1) {
    fileName.Remove(0,15);
    fileName = hadoopDoor + fileName;
  }
  else if (fileName.Index("/cms/store") != -1) {
    fileName.Remove(0,4);
    fileName = hadoopDoor + fileName;
  }
  
  printf("\n Opening: %s\n\n",fileName.Data());
  TFile* f       = TFile::Open(fileName.Data());

  // Simplest access to total number of events
  long long nAll = -1;
  TH1F* h1 = (TH1F*)f->Get("htotal");
  if (h1)
    nAll = h1->GetEntries();
  
  // Now deal with trees
  TTree *tree = 0, *allTree = 0;

  tree = (TTree*) f->FindObjectAny("events");
  allTree  = (TTree*) f->FindObjectAny("all");

  if (tree && allTree) {
    if (nAll < 0)
      nAll = allTree->GetEntries();
    printf("XX-CATALOG-XX 0000 %s %lld %lld %d %d %d %d\n",
	   fileName.Data(),tree->GetEntries(),nAll,1,1,1,1);
    return;
  }

  if (tree) {
    if (nAll < 0)
      nAll = tree->GetEntries();
    printf("XX-CATALOG-XX 0000 %s %lld %lld %d %d %d %d\n",
	   fileName.Data(),tree->GetEntries(),nAll,1,1,1,1);
    return;
  }

  tree    = (TTree*) f->FindObjectAny("Events");
  if (tree) {
    if (nAll < 0)
      nAll = tree->GetEntries();
    printf("XX-CATALOG-XX 0000 %s %lld %lld %d %d %d %d\n",
	   fileName.Data(),tree->GetEntries(),nAll,1,1,1,1);
    return;
  }

  allTree = (TTree*) f->FindObjectAny("AllEvents");
  if (tree && allTree) {
    if (nAll < 0)
      nAll = allTree->GetEntries();
    printf("XX-CATALOG-XX 0000 %s %lld %lld %d %d %d %d\n",
	   fileName.Data(),tree->GetEntries(),nAll,1,1,1,1);
    return;
  }

  allTree = (TTree*) f->FindObjectAny("T");
  if (allTree) {
    if (nAll < 0)
      nAll = allTree->GetEntries();
    printf("XX-CATALOG-XX 0000 %s %lld %lld %d %d %d %d\n",
	   fileName.Data(),nAll,nAll,1,1,1,1);
    return;
  }
}

//--------------------------------------------------------------------------------------------------
void reset()
{
}
