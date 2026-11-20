/* English / Konkani switch for the citizen pages.

   It swaps text for the Konkani below, using exact matches on the English the pages already show, so no page
   needs data attributes. Switching back restores the English. Text that comes from the server (a complaint
   description, a message already written in the complaint's language) is left as it is.

   The Konkani here is a first draft and has NOT been reviewed by a native speaker. Check it before real use. */
(function () {
  "use strict";

  const KEY = "portal_lang";

  const KOK = {
    "Goa Grievance Tracker": "गोंय तक्रार मागोवो",
    "Follow-up and reminders for citizen grievances": "नागरिकांच्या तक्रारींचो पाठपुरावो आनी याद",
    "Made by Abhinav Reddy and Tony Madhuri. Student prototype. Not an official government system.": "अभिनव रेड्डी आनी टोनी मधुरी हांणी तयार केला. विद्यार्थ्यांचो नमुनो. सरकारी अधिकृत यंत्रणा न्हय.",
    "Unofficial demo": "अनधिकृत डेमो",
    "Language": "भास",
    "Install this app on your phone": "ही ॲप तुमच्या फोनाचेर घालात",
    "It opens full screen with its own icon. Nothing to download from a store.": "ती आपल्या आयकॉनासयत पुराय स्क्रीनार उबी जाता. स्टोअरांतल्यान कांयच डाउनलोड करचें ना.",
    "Install app": "ॲप घालात",
    "Already logged in on this device": "ह्या उपकरणांत आधींच लॉगिन जालां",
    "To use another role here, pick its tab below and log in. The logins above stay open.": "हांगा दुसरी भूमिका वापरपाक, सकयलो ताब निवडात आनी लॉगिन करात. वयले लॉगिन तशेच उरतात.",
    "Sign in as another role": "दुसऱ्या भूमिकेंत लॉगिन करात",
    "How it works": "हें कशें चलता",
    "Open on your phone": "तुमच्या फोनाचेर उक्तें करात",
    "In Chrome: tap the menu (three dots), then Install app or Add to Home screen.": "क्रोमांत: मेनू (तीन टिपके) दाबात, मागीर ॲप घालात वा होम स्क्रीनाक जोडात दाबात.",
    "On iPhone: tap the Share icon in Safari, then Add to Home Screen.": "आयफोनाचेर: सफारींत शेअर आयकॉन दाबात, मागीर होम स्क्रीनाक जोडात दाबात.",
    "Main": "मुखेल",
    "Home": "मुखेल पान",
    "Register Complaint": "तक्रार नोंद करात",
    "Track Complaint": "तक्रारीचो मागोवो",
    "Services": "सेवा",
    "How It Works": "हें कशें चलता",
    "Your account": "तुमचें खातें",
    "Your details": "तुमची म्हायती",
    "Log out": "लॉग आऊट",
    "Name": "नांव",
    "Mobile": "मोबायल",
    "Address": "पत्तो",
    "Zone": "वाठार",
    "Ward": "वॉर्ड",
    "Sign-up": "नोंदणी",
    "User sign-up": "वापरपी नोंदणी",
    "Worker sign-up": "कामगार नोंदणी",
    "Officer sign-up": "अधिकारी नोंदणी",
    "User Sign-up": "वापरपी नोंदणी",
    "Worker Sign-up": "कामगार नोंदणी",
    "Officer Sign-up": "अधिकारी नोंदणी",
    "Registered once": "एकदांच नोंदणी",
    "Auto reminders": "आपशींच याद",
    "Escalated on time": "वेळार वयल्या पातळेक",
    "Your voice matters": "तुमचो आवाज म्हत्वाचो",
    "Choose how to log in": "लॉगिन कशें करचें तें निवडात",
    "User Login": "वापरपी लॉगिन",
    "Worker Login": "कामगार लॉगिन",
    "Officer Login": "अधिकारी लॉगिन",
    "Mobile number": "मोबायल क्रमांक",
    "Enter your 10-digit mobile number": "तुमचो 10 आंकड्यांचो मोबायल क्रमांक घालात",
    "You get a 6-digit code by SMS or WhatsApp on this number. If it is not set up on the server, the code appears here instead.": "ह्या क्रमांकार तुमकां एसएमएस वा वॉट्सॲपान 6 आंकड्यांचो कोड मेळटा. सर्व्हरार हें थारायलें ना जाल्यार कोड हांगाच दिसता.",
    "Workers get a 6-digit code by SMS or WhatsApp on this number. If it is not set up on the server, the code appears here instead.": "कामगारांक ह्या क्रमांकार एसएमएस वा वॉट्सॲपान 6 आंकड्यांचो कोड मेळटा. सर्व्हरार हें थारायलें ना जाल्यार कोड हांगाच दिसता.",
    "Send me a code": "म्हाका कोड धाडात",
    "Sign up as a citizen": "नागरिक म्हणून नोंदणी करात",
    "Prefer WhatsApp?": "वॉट्सॲप जाय?",
    "Chat with us on WhatsApp": "आमकां वॉट्सॲपार संवाद साधात",
    "Code": "कोड",
    "Enter the 6-digit code": "6 आंकड्यांचो कोड घालात",
    "Log in": "लॉगिन करात",
    "Use a different mobile number": "दुसरो मोबायल क्रमांक वापरात",
    "Don't have an account?": "खातें ना?",
    "Click here to sign up": "नोंदणी करपाक हांगा दाबात",
    "Sign up as a worker": "कामगार म्हणून नोंदणी करात",
    "New worker?": "नवो कामगार?",
    "Username": "वापरपी नांव",
    "Your officer username": "तुमचें अधिकारी वापरपी नांव",
    "Password": "पासवर्ड",
    "Officer logins end at midnight every day (India time).": "अधिकाऱ्यांचे लॉगिन दर दिसा मध्यानरात्री (भारतीय वेळ) सोंपतात.",
    "New officer?": "नवो अधिकारी?",
    "How the portal works": "पोर्टल कशें चलता",
    "Previous": "फाटलें",
    "Next": "फुडें",
    "Enter your details below to create your account.": "तुमचें खातें तयार करपाक सकयल तुमची म्हायती घालात.",
    "Fields marked with": "खुणा केल्ले फील्ड",
    "are mandatory": "जाय आसात",
    "Enter your name": "तुमचें नांव घालात",
    "House No. / Street / Area": "घर क्रमांक / रस्तो / वाठार",
    "Used to find your zone. Include your area name.": "तुमचो वाठार सोदपाक वापरतात. तुमच्या वाठाराचें नांव घालात.",
    "Loading zones ...": "वाठार लोड जाता ...",
    "Select a zone ...": "वाठार निवडात ...",
    "Ward / Area": "वॉर्ड / वाठार",
    "Select a zone first": "पयलीं वाठार निवडात",
    "Select your ward ...": "तुमचो वॉर्ड निवडात ...",
    "Country": "देश",
    "State": "राज्य",
    "District": "जिल्लो",
    "You log in with a code to this number.": "तुमी ह्या क्रमांकाक येवपी कोडान लॉगिन करतात.",
    "Reset": "रिसेट",
    "Submit": "सादर करात",
    "Already signed up?": "आधींच नोंदणी केल्या?",
    "Log in with your mobile number": "तुमच्या मोबायल क्रमांकान लॉगिन करात",
    "Report water, road, health, sanitation and police problems. Follow every step and get reminders until it is resolved.": "उदक, रस्ते, आरोग्य, स्वच्छताय आनी पोलीस समस्यांची तक्रार करात. दर एक पावल पळयात आनी तक्रार सुटमेरेन याद मेळयात.",
    "Common Services": "सामकी सेवा",
    "Report a problem to the right department of Goa.": "गोंयच्या योग्य खात्याक समस्या कळयात.",
    "Register a complaint": "तक्रार नोंद करात",
    "Drinking Water": "पियेवेचें उदक",
    "No water, low pressure, a broken pipe or dirty water.": "उदक ना, कमी दाब, फुटलो पायप वा घाण उदक.",
    "Roads and Potholes": "रस्ते आनी खळगे",
    "A damaged road, pothole or blocked footpath.": "मोडिल्लो रस्तो, खळगो वा बंद जाल्लो पदपथ.",
    "Streetlights": "रस्त्यावयले दिवे",
    "A streetlight that is off, flickering or damaged.": "बंद आशिल्लो, लुकलुकपी वा मोडिल्लो रस्त्यावयलो दिवो.",
    "Sanitation and Drains": "स्वच्छताय आनी गटारां",
    "Garbage not collected, a blocked drain or a local tax issue.": "कचरो उखलूंक ना, गटार बंद वा स्थानीक करांचो प्रस्न.",
    "Health and Hospitals": "आरोग्य आनी इस्पितळां",
    "A problem at a government hospital or health centre.": "सरकारी इस्पितळांत वा आरोग्य केंद्रांत समस्या.",
    "Police Complaint": "पोलीस तक्रार",
    "Cybercrime, fraud, lost property or traffic. We only register and track it.": "सायबर गुन्हो, फसवणूक, हरयिल्ली वस्तू वा वाहतूक. आमी फकत नोंद करतात आनी मागोवो घेतात.",
    "Your complaints in numbers": "तुमच्या तक्रारी आंकड्यांनी",
    "Your Complaints in Numbers": "तुमच्या तक्रारी आंकड्यांनी",
    "From your account. Updates on its own.": "तुमच्या खात्यांतल्यान. आपशींच नवें जाता.",
    "Registered": "नोंद जाल्ल्यो",
    "In progress": "चालू आसा",
    "Waiting for you": "तुमची वाट पळयता",
    "Resolved": "सुटल्यो",
    "From complaint to resolution, in four simple steps.": "तक्रारीपसून सोडवणुकेमेरेन, चार सोप्या पावलांनी.",
    "1. Register": "1. नोंद",
    "Describe the problem in English or Konkani. Add a photo or document if you have one.": "समस्या इंग्रजींत वा कोंकणींत सांगात. फोटो वा कागद आसल्यार जोडात.",
    "2. Auto-route": "2. आपशींच धाडप",
    "It goes to the right department and officer for your area.": "ती तुमच्या वाठारांतल्या योग्य खात्याक आनी अधिकाऱ्याक वता.",
    "3. Track and get reminders": "3. मागोवो घेवन याद मेळयात",
    "See the status and history. Reminders go out before the time limit ends.": "स्थिती आनी इतिहास पळयात. वेळमर्याद सोंपचे पयलीं याद वता.",
    "4. Escalate or resolve": "4. वयली पातळी वा सोडवणूक",
    "If the time limit passes, it moves up to the next officer. You confirm the fix.": "वेळमर्याद सोंपल्यार ती फुडल्या अधिकाऱ्याक वता. सोडवणूक जाल्ली तुमी खात्री करतात.",
    "Your Complaints": "तुमच्यो तक्रारी",
    "When an officer marks a complaint resolved, confirm here whether the problem is fixed.": "अधिकारी तक्रार सुटली अशें नोंद करता तेन्ना समस्या सुटली काय तें हांगा खात्री करात.",
    "Live": "थेट",
    "You have not registered a complaint yet.": "तुमी अजून तक्रार नोंद केल्ली ना.",
    "You have not registered a complaint yet. Your complaints will appear here.": "तुमी अजून तक्रार नोंद केल्ली ना. तुमच्यो तक्रारी हांगा दिसतले.",
    "Tell us what is wrong. The complaint goes to the officer for your field and ward.": "कितें चुकलां तें सांगात. तक्रार तुमच्या खात्याच्या आनी वॉर्डाच्या अधिकाऱ्याक वता.",
    "Today": "आज",
    "Type of complaint": "तक्रारीचो प्रकार",
    "Emergency": "आणीबाणी",
    "Fire, rescue, gas leak, a fallen live wire or anyone in danger right now.": "आग, सुटका, गॅस गळती, पडिल्लो वीज तार वा आत्तां धोक्यांत आशिल्लो कोणूय.",
    "Not emergency": "आणीबाणी न्हय",
    "Water, drains, garbage, roads and other everyday civic problems.": "उदक, गटारां, कचरो, रस्ते आनी हेर दिसाचे नागरी प्रस्न.",
    "Police complaint": "पोलीस तक्रार",
    "Cybercrime, fraud, lost property, traffic and public safety. We only register and track it.": "सायबर गुन्हो, फसवणूक, हरयिल्ली वस्तू, वाहतूक आनी सार्वजनीक सुरक्षा. आमी फकत नोंद करतात आनी मागोवो घेतात.",
    "If a life is at risk, call 112 first. Then fill in this form so the right officer sees it.": "जिवाक धोको आसल्यार पयलीं 112 वयर फोन करात. मागीर योग्य अधिकाऱ्याक दिसचें म्हणून हो अर्ज भरात.",
    "Choose the problem": "समस्या निवडात",
    "Photos of the problem": "समस्येचे फोटो",
    "Photos of the problem (optional)": "समस्येचे फोटो (ऐच्छीक)",
    "Optional. Add up to 3 photos if you have them. JPEG, PNG or WebP. Large photos are made smaller on your phone before they are sent.": "ऐच्छीक. आसल्यार 3 फोटो जोडात. JPEG, PNG वा WebP. व्हड फोटो धाडचे पयलीं तुमच्या फोनाचेर नान्यो केल्ले आसतात.",
    "Photos and documents": "फोटो आनी कागद",
    "Upload 3 photos. JPEG, PNG or WebP. Large photos are made smaller on your phone before they are sent.": "3 फोटो अपलोड करात. JPEG, PNG वा WebP. व्हड फोटो धाडचे पयलीं तुमच्या फोनाचेर नान्यो केल्ले आसतात.",
    "0 of 3 photos added": "3 पैकी 0 फोटो जोडले",
    "Address of the problem": "समस्येचो पत्तो",
    "+ Add address": "+ पत्तो जोडात",
    "Add a new address": "नवो पत्तो जोडात",
    "Full name": "पुराय नांव",
    "House, flat or building": "घर, फ्लॅट वा इमारत",
    "For example: No. 12, Ground floor": "उदाहरण: क्र. 12, तळमजलो",
    "Street or road": "रस्तो वा मार्ग",
    "For example: 4th Main Road": "उदाहरण: चवथो मुखेल रस्तो",
    "Area": "वाठार",
    "For example: Super Market area": "उदाहरण: बाजार वाठार",
    "City": "शार",
    "Landmark": "खूण",
    "For example: opposite the bus stop": "उदाहरण: बस स्थानकाच्या मुखार",
    "Cancel": "रद्द करात",
    "Use this address": "हो पत्तो वापरात",
    "Describe the problem": "समस्या सांगात",
    "For example: no water has come to our street for three days.": "उदाहरण: आमच्या रस्त्याचेर तीन दीस उदक येवंक ना.",
    "of 2000 characters. Say where the problem is and since when.": "2000 अक्षरांतलें. समस्या खंय आसा आनी केन्नासावन तें सांगात.",
    "Use the local model to help sort the complaint, if it is running on this computer": "हो संगणक चालू आसल्यार, तक्रार वर्गीकरणाक स्थानीक मॉडेल वापरात",
    "Your complaint is registered. Complaint ID:": "तुमची तक्रार नोंद जाल्या. तक्रार क्रमांक:",
    "Keep this complaint ID. Use it on Track Complaint to follow your complaint.": "हो तक्रार क्रमांक सांबाळून दवरात. तक्रारीचो मागोवो घेवपाक तो 'तक्रारीचो मागोवो' हांगा वापरात.",
    "Message for you": "तुमखातीर संदेश",
    "Track this complaint": "ह्या तक्रारीचो मागोवो घेयात",
    "Register another": "दुसरी नोंद करात",
    "Back to home": "मुखेल पानाक परतात",
    "From the agents": "एजंटां कडल्यान",
    "Message from the complaint router about this complaint.": "ह्या तक्रारीविशीं तक्रार राउटराचो संदेश.",
    "Time limits for your complaint": "तुमच्या तक्रारीचे वेळमर्याद",
    "What happens next": "फुडें कितें जाता",
    "A field worker accepts your complaint. You will see \"Allotted\" and \"Work in progress\".": "एक क्षेत्र कामगार तुमची तक्रार स्वीकारता. तुमकां \"सोंपयलें\" आनी \"काम चालू\" दिसतलें.",
    "When the work is done, a code comes to your mobile. Give it to the worker only if the problem is fixed.": "काम जाल्यार तुमच्या मोबायलाचेर कोड येता. समस्या सुटल्यारच तो कामगाराक दिवचो.",
    "If the time limit passes, the officers get a notice and the complaint moves up to the next officer.": "वेळमर्याद सोंपल्यार अधिकाऱ्यांक नोटीस वता आनी तक्रार फुडल्या अधिकाऱ्याक वता.",
    "Your complaints": "तुमच्यो तक्रारी",
    "Loading ...": "लोड जाता ...",
    "Completed": "सोंपल्यो",
    "Not completed": "सोंपल्यो ना",
    "None yet": "अजून कांयच ना",
    "Every Complaint Followed Up": "दर एका तक्रारीचो पाठपुरावो",
    "for Every Taluka in": "दर एका तालुक्यांत",
    "Goa": "गोंय",
    "Documents or photos (optional)": "कागद वा फोटो (ऐच्छीक)",
    "You may add up to 3 files: JPEG, PNG, WebP or PDF, each under 4 MB. Do not add anything you do not want the police station to see.": "तुमी 3 फायली जोडूं शकतात: JPEG, PNG, WebP वा PDF, दरेक 4 MB सावन उणी. पोलीस ठाणें पळोवचें ना अशें कांयच जोडूं नाकात.",
    "Add photo": "फोटो जोडात",
    "Add file": "फायल जोडात",
    "Change": "बदलात",
    "Your registered address": "तुमचो नोंद केल्लो पत्तो",
    "Problem": "समस्या",
    "Not given": "दिल्लें ना",
    "Write a note first.": "पयलीं एक टिपण बरयात.",
    "Add 3 photos of the problem.": "समस्येचे 3 फोटो जोडात.",
    "Open. Being handled.": "उक्ती. हाताळटात.",
    "Allotted": "सोंपयलें",
    "Waiting for a worker": "कामगाराची वाट पळयता",
    "Work in progress": "काम चालू",
    "The worker is on it": "कामगार तातूंत आसा",
    "Not yet": "अजून ना",
    "Problem fixed": "समस्या सुटली",
    "Confirm the fix below": "सकयल खात्री करात",
    "Waiting for you": "तुमची वाट पळयता",
    "Department": "खातें",
    "Time limit": "वेळमर्याद",
    "Zone and ward": "वाठार आनी वॉर्ड",
    "Taluka and ward": "तालुको आनी वॉर्ड",
    "Worker": "कामगार",
    "Not allotted yet": "अजून सोंपयलें ना",
    "Office in charge": "जबाबदार कार्यालय",
    "Officer": "अधिकारी",
    "Registered on": "नोंद जाल्ली तारीख",
    "Landmark": "खूण",
    "None": "कांयच ना",
    "Not recorded": "नोंद ना",
    "Not running": "चालू ना",
    "Track →": "मागोवो →",
    "Close the complaint": "तक्रार बंद करात",
    "Yes, it is fixed": "होय, सुटली",
    "No, still not fixed": "ना, अजून सुटूंक ना",
    "An officer has marked this complaint resolved. Is the problem really fixed?": "अधिकाऱ्यान ही तक्रार सुटली अशें नोंद केलां. समस्या खरेंच सुटली?",
    "Comment (optional)": "टिपणी (ऐच्छीक)",
    "Comment": "टिपणी",
    "No messages yet.": "अजून संदेश ना.",
    "Code for the worker:": "कामगाराखातीर कोड:",
    "Emergency Rescue": "आणीबाणी सुटका",
    "Fire and smoke emergencies": "आग आनी धुराची आणीबाणी",
    "Ambulance and medical emergencies": "रुग्णवाहिका आनी वैद्यकीय आणीबाणी",
    "LPG gas leakage": "एलपीजी गॅस गळती",
    "Hazardous gas or chemical leakage": "धोकादायक गॅस वा रसायनाची गळती",
    "Flood rescue and evacuation": "पूर सुटका आनी स्थलांतर",
    "Building collapse and trapped persons": "इमारत कोसळप आनी अडकल्ले लोक",
    "Electrical hazards and fallen live wires": "वीज धोके आनी पडिल्ल्यो वीज तारो",
    "Road accidents requiring rescue": "सुटकेची गरज आशिल्ले रस्ते अपघात",
    "People trapped in lifts or confined spaces": "लिफ्टांत वा अरुंद जायेंत अडकल्ले लोक",
    "Tree falls blocking access or threatening lives": "वाट आडावपी वा जिवाक धोको दिवपी रूख पडप",
    "Drowning and water rescue": "बुडप आनी उदकांतली सुटका",
    "Landslides and structural hazards": "दरड कोसळप आनी बांधकाम धोके",
    "Water Supply": "उदक पुरवण",
    "Drainage and Sewerage": "गटारां आनी सांडपाणी",
    "Garbage and Sanitation": "कचरो आनी स्वच्छताय",
    "Roads and Footpaths": "रस्ते आनी पदपथ",
    "Flooding and Waterlogging": "पूर आनी उदक सांचप",
    "Public Health and Stray Animals": "सार्वजनीक आरोग्य आनी भटकीं जनावरां",
    "Parks and Public Infrastructure": "उद्यानां आनी सार्वजनीक सुविधा",
    "Municipal Services and Taxes": "नगरपालिका सेवा आनी कर",
    "Other Complaints": "हेर तक्रारी",
    "Cybercrime and online fraud": "सायबर गुन्हो आनी ऑनलायन फसवणूक",
    "Financial fraud": "आर्थिक फसवणूक",
    "Lost property": "हरयिल्ली वस्तू",
    "Public safety and traffic": "सार्वजनीक सुरक्षा आनी वाहतूक",
    "Complaint involving individuals": "व्यक्तींविशीं तक्रार",
    "This system only registers and tracks your complaint. Whether an offence took place, and whether an FIR is registered, is decided only by authorised police officials.": "ही यंत्रणा फकत तुमची तक्रार नोंद करता आनी तिचो मागोवो घेता. गुन्हो घडलो काय आनी एफआयआर नोंद जाता काय हें फकत अधिकृत पोलीस अधिकारीच थारायतात.",
    "Type": "प्रकार",
    "Department": "खातें",
    "Follow-up due": "पाठपुरावो देय",
    "Language": "भास",
    "Allotted · Work in progress": "सोंपयलें · काम चालू",
    "Rejected · In progress": "न्हयकारलें · चालू",
    "Done": "जालें",
    "Now": "आत्तां",
    "Not needed": "गरज ना",
    "Track Your": "तुमच्या",
    "Complaint": "तक्रारीचो मागोवो",
    "Enter your complaint ID to see where it is, who is working on it, and its time limit.": "ती खंय आसा, कोण तातूंत काम करता आनी तिची वेळमर्याद कितली तें पळोवपाक तुमचो तक्रार क्रमांक घालात.",
    "Enter your complaint ID, for example CMP-20261018-1234": "तुमचो तक्रार क्रमांक घालात, उदाहरण CMP-20261018-1234",
    "Complaint ID": "तक्रार क्रमांक",
    "Track": "मागोवो",
    "Search above, or choose one of your complaints below.": "वयल्यान सोदात, वा सकयल तुमची एक तक्रार निवडात.",
    "Your complaints:": "तुमच्यो तक्रारी:",
    "Progress": "प्रगती",
    "Details": "तपशील",
    "Your complaint": "तुमची तक्रार",
    "Time limits from the router": "राउटराचे वेळमर्याद",
    "Message from the complaint router": "तक्रार राउटराचो संदेश",
    "History": "इतिहास",
    "Messages to you": "तुमकां संदेश",
    "Documents": "कागद",
  };

  // Text with numbers or names in it: [pattern, function that builds the Konkani].
  const PATTERNS = [
    [/^(\d+) of (\d+) photos added$/, (m) => `${m[2]} पैकी ${m[1]} फोटो जोडले`],
    [/^(\d+) of (\d+) photos added \(optional\)$/, (m) => `${m[2]} पैकी ${m[1]} फोटो जोडले (ऐच्छीक)`],
    [/^(\d+) of (\d+) files added$/, (m) => `${m[2]} पैकी ${m[1]} फायली जोडल्यो`],
    [/^Time limit: (.+)$/, (m) => `वेळमर्याद: ${m[1]}`],
    [/^Counting down to (.+)$/, (m) => `शेवटची वेळ: ${m[1]}`],
    [/^Hello, (.+)$/, (m) => `नमस्कार, ${m[1]}`],
    [/^Welcome, (.+)$/, (m) => `स्वागत, ${m[1]}`],
    [/^Today: (.+)$/, (m) => `आज: ${m[1]}`],
    [/^Photo (\d+)$/, (m) => `फोटो ${m[1]}`],
    [/^(\d+) of (\d+) files added \(optional\)$/, (m) => `${m[2]} पैकी ${m[1]} फायली जोडल्यो (ऐच्छीक)`],
    [/^(.+) \((.+)\)$/, (m) => {
      const a = KOK[m[1]], b = KOK[m[2]];   // "Complaint type (Department)" in the lists of complaints
      return a && b ? `${a} (${b})` : null;
    }],
    [/^(.+) zone$/, (m) => { const a = KOK[m[1]]; return a ? `${a} वाठार` : null; }],
    [/^(.+) - Goa Grievance Tracker$/, (m) => `${translate(m[1])} - गोंय तक्रार मागोवो`],
  ];

  let lang = "en";
  const originals = new WeakMap();   // text node -> the English it had
  const written = new WeakMap();     // text node -> the Konkani this script wrote
  const attrOriginals = new WeakMap();   // element -> { attribute: English }
  const ATTRS = ["placeholder", "title", "aria-label"];
  const SKIP = new Set(["SCRIPT", "STYLE", "TEXTAREA", "OPTION_VALUE"]);

  function translate(text) {
    const key = text.trim();
    if (!key) return text;
    let out = KOK[key];
    if (out === undefined) {
      for (const [pattern, build] of PATTERNS) {
        const m = key.match(pattern);
        if (m) { out = build(m); if (out) break; out = undefined; }
      }
    }
    if (out === undefined) return text;
    const lead = text.match(/^\s*/)[0];
    const trail = text.match(/\s*$/)[0];
    return lead + out + trail;
  }

  function skipped(node) {
    for (let p = node.parentNode; p; p = p.parentNode) {
      if (p.nodeType === 1 && (SKIP.has(p.tagName) || p.hasAttribute("data-no-i18n"))) return true;
    }
    return false;
  }

  function doText(node) {
    if (skipped(node)) return;
    if (lang === "kok") {
      if (written.get(node) === node.nodeValue) return;   // our own change
      const english = node.nodeValue;
      const kok = translate(english);
      if (kok !== english) {
        originals.set(node, english);
        written.set(node, kok);
        node.nodeValue = kok;
      }
    } else if (originals.has(node) && written.get(node) === node.nodeValue) {
      node.nodeValue = originals.get(node);
      originals.delete(node);
      written.delete(node);
    }
  }

  function doAttrs(element) {
    if (!element.getAttribute) return;
    for (const name of ATTRS) {
      const value = element.getAttribute(name);
      if (value === null) continue;
      let saved = attrOriginals.get(element);
      if (lang === "kok") {
        if (saved && saved[name] && saved[name].kok === value) continue;
        const kok = translate(value);
        if (kok !== value) {
          saved = saved || {};
          saved[name] = { en: value, kok: kok };
          attrOriginals.set(element, saved);
          element.setAttribute(name, kok);
        }
      } else if (saved && saved[name] && saved[name].kok === value) {
        element.setAttribute(name, saved[name].en);
        delete saved[name];
      }
    }
  }

  function walk(root) {
    if (root.nodeType === 3) { doText(root); return; }
    if (root.nodeType !== 1 || SKIP.has(root.tagName)) return;
    doAttrs(root);
    for (const child of root.childNodes) walk(child);
  }

  function doTitle() {
    const title = document.querySelector("title");
    if (!title || !title.firstChild) return;
    doText(title.firstChild);
  }

  const observer = new MutationObserver((records) => {
    for (const record of records) {
      if (record.type === "characterData") doText(record.target);
      else if (record.type === "attributes") doAttrs(record.target);
      else record.addedNodes.forEach(walk);
    }
  });

  function apply(next) {
    lang = next === "kok" ? "kok" : "en";
    document.documentElement.lang = lang;
    walk(document.body);
    doTitle();
    const select = document.getElementById("lang");
    if (select && select.value !== lang) select.value = lang;
    try { localStorage.setItem(KEY, lang); } catch (err) { /* not saved; English next time */ }
    window.dispatchEvent(new CustomEvent("portal-lang", { detail: lang }));
  }

  // Pages other than the first screen have no language box; add one next to the account menu.
  function ensureSelect() {
    if (document.getElementById("lang")) return;
    const holder = document.querySelector(".top-right") || document.querySelector(".topbar .container");
    if (!holder) return;
    const label = document.createElement("label");
    label.className = "lang";
    label.setAttribute("data-no-i18n", "");
    label.innerHTML = '<svg class="icon" aria-hidden="true"><use href="/assets/icons.svg#globe"/></svg>' +
      '<select id="lang" aria-label="Language"><option value="en">English</option><option value="kok">कोंकणी</option></select>';
    holder.insertBefore(label, holder.firstChild);
  }

  // Office and complaint-type names come from the district's charter, with their Konkani.
  function loadNames() {
    if (!window.fetch) return;
    fetch("/api/config", { credentials: "same-origin" })
      .then((response) => (response.ok ? response.json() : null))
      .then((config) => {
        if (!config || !config.konkani_names) return;
        for (const key of Object.keys(config.konkani_names)) if (!(key in KOK)) KOK[key] = config.konkani_names[key];
        if (lang === "kok") walk(document.body);
      })
      .catch(() => { /* the pages still work in English */ });
  }

  function start() {
    ensureSelect();
    loadNames();
    const select = document.getElementById("lang");
    if (select) select.addEventListener("change", (event) => apply(event.target.value));
    let saved = "en";
    try { saved = localStorage.getItem(KEY) || "en"; } catch (err) { saved = "en"; }
    if (new URLSearchParams(window.location.search).get("lang") === "kok") saved = "kok";
    apply(saved);
    observer.observe(document.documentElement, {
      childList: true, subtree: true, characterData: true,
      attributes: true, attributeFilter: ATTRS,
    });
  }

  window.PortalI18n = {
    get lang() { return lang; },
    set: apply,
    t: (text) => (lang === "kok" ? translate(text) : text),
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
