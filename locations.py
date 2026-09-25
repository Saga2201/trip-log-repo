"""Indian states and major cities for dropdown selection."""

STATES_CITIES: dict[str, list[str]] = {
    'Andhra Pradesh': [
        'Visakhapatnam', 'Vijayawada', 'Guntur', 'Nellore', 'Kurnool',
        'Rajahmundry', 'Kakinada', 'Tirupati', 'Anantapur', 'Kadapa',
        'Eluru', 'Ongole', 'Nandyal', 'Machilipatnam', 'Adoni',
        'Tenali', 'Proddatur', 'Chittoor', 'Hindupur', 'Bhimavaram',
    ],
    'Arunachal Pradesh': [
        'Itanagar', 'Naharlagun', 'Pasighat', 'Bomdila', 'Tawang',
        'Ziro', 'Tezu', 'Along', 'Changlang', 'Khonsa',
    ],
    'Assam': [
        'Guwahati', 'Silchar', 'Dibrugarh', 'Jorhat', 'Nagaon',
        'Tinsukia', 'Tezpur', 'Bongaigaon', 'Dhubri', 'Diphu',
        'Goalpara', 'Golaghat', 'Lakhimpur', 'Sivasagar', 'Karimganj',
        'Nalbari', 'Barpeta', 'Kokrajhar', 'Haflong',
    ],
    'Bihar': [
        'Patna', 'Gaya', 'Bhagalpur', 'Muzaffarpur', 'Purnia',
        'Darbhanga', 'Arrah', 'Begusarai', 'Katihar', 'Munger',
        'Chapra', 'Samastipur', 'Hajipur', 'Sasaram', 'Bihar Sharif',
        'Sitamarhi', 'Motihari', 'Siwan', 'Kishanganj', 'Bettiah',
        'Aurangabad', 'Jehanabad', 'Nawada',
    ],
    'Chhattisgarh': [
        'Raipur', 'Bhilai', 'Bilaspur', 'Korba', 'Durg',
        'Rajnandgaon', 'Jagdalpur', 'Raigarh', 'Ambikapur', 'Dhamtari',
        'Mahasamund', 'Kawardha', 'Kondagaon', 'Kanker', 'Janjgir',
    ],
    'Goa': [
        'Panaji', 'Margao', 'Vasco da Gama', 'Mapusa', 'Ponda',
        'Bicholim', 'Curchorem', 'Sanquelim', 'Canacona',
    ],
    'Gujarat': [
        'Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar',
        'Jamnagar', 'Junagadh', 'Gandhinagar', 'Anand', 'Mehsana',
        'Nadiad', 'Morbi', 'Surendranagar', 'Bharuch', 'Vapi',
        'Navsari', 'Veraval', 'Botad', 'Amreli', 'Porbandar',
        'Dahod', 'Godhra', 'Palanpur', 'Patan', 'Idar',
        'Gandhidham', 'Kandla', 'Dwarka', 'Somnath', 'Deesa',
    ],
    'Haryana': [
        'Faridabad', 'Gurugram', 'Panipat', 'Ambala', 'Yamunanagar',
        'Rohtak', 'Hisar', 'Karnal', 'Sonipat', 'Panchkula',
        'Bhiwani', 'Sirsa', 'Bahadurgarh', 'Jind', 'Thanesar',
        'Kaithal', 'Rewari', 'Palwal', 'Narnaul', 'Fatehabad',
    ],
    'Himachal Pradesh': [
        'Shimla', 'Dharamshala', 'Solan', 'Mandi', 'Palampur',
        'Baddi', 'Nahan', 'Kullu', 'Hamirpur', 'Una',
        'Chamba', 'Bilaspur', 'Kangra', 'Manali', 'Rampur',
    ],
    'Jharkhand': [
        'Ranchi', 'Jamshedpur', 'Dhanbad', 'Bokaro', 'Deoghar',
        'Phusro', 'Hazaribagh', 'Giridih', 'Ramgarh', 'Medininagar',
        'Chaibasa', 'Chatra', 'Gumla', 'Lohardaga', 'Pakur',
    ],
    'Karnataka': [
        'Bengaluru', 'Hubli-Dharwad', 'Mysuru', 'Mangaluru', 'Kalaburagi',
        'Belagavi', 'Davangere', 'Ballari', 'Vijayapura', 'Shivamogga',
        'Tumakuru', 'Raichur', 'Bidar', 'Hassan', 'Udupi',
        'Chitradurga', 'Hospet', 'Gadag', 'Bagalkot', 'Chikkamagaluru',
        'Mandya', 'Kolar', 'Yadgir', 'Koppal', 'Haveri',
    ],
    'Kerala': [
        'Thiruvananthapuram', 'Kochi', 'Kozhikode', 'Thrissur', 'Kollam',
        'Palakkad', 'Alappuzha', 'Kannur', 'Kottayam', 'Kasaragod',
        'Malappuram', 'Pathanamthitta', 'Idukki', 'Wayanad', 'Ernakulam',
        'Thalassery', 'Tirur', 'Ponnani', 'Chalakudy',
    ],
    'Madhya Pradesh': [
        'Indore', 'Bhopal', 'Jabalpur', 'Gwalior', 'Ujjain',
        'Sagar', 'Dewas', 'Satna', 'Ratlam', 'Rewa',
        'Murwara', 'Singrauli', 'Burhanpur', 'Khandwa', 'Bhind',
        'Chhindwara', 'Guna', 'Shivpuri', 'Vidisha', 'Chhatarpur',
        'Damoh', 'Mandsaur', 'Khargone', 'Neemuch', 'Pithampur',
        'Hoshangabad', 'Itarsi', 'Sehore', 'Betul', 'Seoni',
    ],
    'Maharashtra': [
        'Mumbai', 'Pune', 'Nagpur', 'Thane', 'Nashik',
        'Aurangabad', 'Solapur', 'Kolhapur', 'Amravati', 'Nanded',
        'Sangli', 'Satara', 'Latur', 'Jalgaon', 'Akola',
        'Dhule', 'Chandrapur', 'Parbhani', 'Jalna', 'Yavatmal',
        'Ahmednagar', 'Bid', 'Osmanabad', 'Buldhana', 'Washim',
        'Wardha', 'Bhandara', 'Gondia', 'Ratnagiri', 'Sindhudurg',
        'Raigad', 'Navi Mumbai', 'Vasai-Virar', 'Bhiwandi', 'Malegaon',
        'Kalyan', 'Ulhasnagar', 'Mira-Bhayandar',
    ],
    'Manipur': [
        'Imphal', 'Thoubal', 'Bishnupur', 'Churachandpur', 'Senapati',
        'Ukhrul', 'Chandel', 'Tamenglong', 'Moreh',
    ],
    'Meghalaya': [
        'Shillong', 'Tura', 'Cherrapunji', 'Nongstoin', 'Williamnagar',
        'Jowai', 'Baghmara', 'Resubelpara',
    ],
    'Mizoram': [
        'Aizawl', 'Lunglei', 'Champhai', 'Serchhip', 'Kolasib',
        'Lawngtlai', 'Mamit', 'Saiha',
    ],
    'Nagaland': [
        'Kohima', 'Dimapur', 'Mokokchung', 'Tuensang', 'Wokha',
        'Zunheboto', 'Mon', 'Phek', 'Longleng',
    ],
    'Odisha': [
        'Bhubaneswar', 'Cuttack', 'Rourkela', 'Brahmapur', 'Sambalpur',
        'Puri', 'Balasore', 'Baripada', 'Bhadrak', 'Jharsuguda',
        'Jeypore', 'Barbil', 'Kendujhar', 'Rayagada', 'Koraput',
        'Angul', 'Dhenkanal', 'Phulbani', 'Bolangir', 'Bargarh',
    ],
    'Punjab': [
        'Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda',
        'Mohali', 'Hoshiarpur', 'Batala', 'Pathankot', 'Moga',
        'Abohar', 'Malerkotla', 'Khanna', 'Phagwara', 'Firozpur',
        'Muktsar', 'Barnala', 'Rajpura', 'Sangrur', 'Ropar',
        'Fatehgarh Sahib', 'Kapurthala', 'Gurdaspur', 'Nawanshahr',
    ],
    'Rajasthan': [
        'Jaipur', 'Jodhpur', 'Kota', 'Bikaner', 'Ajmer',
        'Udaipur', 'Bhilwara', 'Alwar', 'Bharatpur', 'Sikar',
        'Pali', 'Sri Ganganagar', 'Hanumangarh', 'Chittorgarh', 'Tonk',
        'Barmer', 'Jaisalmer', 'Jhalawar', 'Bundi', 'Sawai Madhopur',
        'Nagaur', 'Jhunjhunu', 'Dausa', 'Churu', 'Banswara',
        'Dungarpur', 'Karauli', 'Rajsamand', 'Baran', 'Dholpur',
    ],
    'Sikkim': [
        'Gangtok', 'Namchi', 'Gyalshing', 'Mangan', 'Jorethang',
        'Ravangla', 'Singtam',
    ],
    'Tamil Nadu': [
        'Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem',
        'Tirunelveli', 'Tiruppur', 'Ranipet', 'Nagercoil', 'Thanjavur',
        'Vellore', 'Kancheepuram', 'Erode', 'Tiruvannamalai', 'Cuddalore',
        'Karur', 'Dindigul', 'Hosur', 'Nagapattinam', 'Ooty',
        'Kumbakonam', 'Sivakasi', 'Viluppuram', 'Krishnagiri', 'Pollachi',
        'Rajapalayam', 'Thoothukudi', 'Pudukkottai', 'Namakkal', 'Ariyalur',
    ],
    'Telangana': [
        'Hyderabad', 'Warangal', 'Nizamabad', 'Karimnagar', 'Khammam',
        'Ramagundam', 'Mahbubnagar', 'Nalgonda', 'Adilabad', 'Suryapet',
        'Miryalaguda', 'Siddipet', 'Mancherial', 'Jagtial', 'Bhongir',
        'Medak', 'Vikarabad', 'Sangareddy', 'Narayanpet', 'Kothagudem',
    ],
    'Tripura': [
        'Agartala', 'Udaipur', 'Dharmanagar', 'Kailasahar', 'Belonia',
        'Ambassa', 'Khowai', 'Sonamura',
    ],
    'Uttar Pradesh': [
        'Lucknow', 'Kanpur', 'Ghaziabad', 'Agra', 'Meerut',
        'Varanasi', 'Allahabad', 'Bareilly', 'Aligarh', 'Moradabad',
        'Saharanpur', 'Gorakhpur', 'Firozabad', 'Noida', 'Jhansi',
        'Mathura', 'Shahjahanpur', 'Rampur', 'Hapur', 'Sambhal',
        'Farrukhabad', 'Mau', 'Haridwar', 'Etah', 'Mirzapur',
        'Muzaffarnagar', 'Budaun', 'Bulandshahr', 'Bahraich', 'Sitapur',
        'Ayodhya', 'Fatehpur', 'Unnao', 'Rae Bareli', 'Banda',
        'Azamgarh', 'Ballia', 'Bijnor', 'Mainpuri', 'Etawah',
        'Lalitpur', 'Gonda', 'Sultanpur', 'Barabanki', 'Hardoi',
        'Pratapgarh', 'Jaunpur', 'Lakhimpur Kheri',
    ],
    'Uttarakhand': [
        'Dehradun', 'Haridwar', 'Roorkee', 'Haldwani', 'Rudrapur',
        'Kashipur', 'Rishikesh', 'Pithoragarh', 'Ramnagar', 'Nainital',
        'Mussoorie', 'Kotdwar', 'Lansdowne', 'Chamoli', 'Uttarkashi',
    ],
    'West Bengal': [
        'Kolkata', 'Howrah', 'Durgapur', 'Asansol', 'Siliguri',
        'Maheshtala', 'Rajpur Sonarpur', 'South Dumdum', 'Bardhhaman',
        'North Dumdum', 'Haldia', 'Krishnanagar', 'Kharagpur', 'Baharampur',
        'Medinipur', 'Jalpaiguri', 'Alipurduar', 'Cooch Behar', 'Raiganj',
        'Balurghat', 'Malda', 'Bankura', 'Purulia', 'Darjeeling',
        'Ranaghat', 'Kalyani', 'Bally', 'Panihati', 'Titagarh',
    ],
    # Union Territories
    'Andaman and Nicobar Islands': [
        'Port Blair', 'Diglipur', 'Rangat', 'Mayabunder', 'Car Nicobar',
    ],
    'Chandigarh': ['Chandigarh'],
    'Dadra and Nagar Haveli and Daman and Diu': [
        'Silvassa', 'Daman', 'Diu',
    ],
    'Delhi': [
        'New Delhi', 'Delhi', 'Dwarka', 'Rohini', 'Pitampura',
        'Janakpuri', 'Lajpat Nagar', 'Saket', 'Vasant Kunj', 'Noida Extension',
        'Shahdara', 'Preet Vihar', 'Mayur Vihar', 'Karol Bagh', 'Connaught Place',
    ],
    'Jammu and Kashmir': [
        'Srinagar', 'Jammu', 'Anantnag', 'Sopore', 'Baramulla',
        'Bijbehara', 'Tral', 'Pampore', 'Udhampur', 'Kathua',
        'Rajouri', 'Punch', 'Reasi', 'Ramban',
    ],
    'Ladakh': [
        'Leh', 'Kargil', 'Nubra', 'Zanskar', 'Diskit',
    ],
    'Lakshadweep': [
        'Kavaratti', 'Agatti', 'Minicoy', 'Andrott',
    ],
    'Puducherry': [
        'Puducherry', 'Karaikal', 'Mahe', 'Yanam',
    ],
}

ALL_STATES: list[str] = sorted(STATES_CITIES.keys())
