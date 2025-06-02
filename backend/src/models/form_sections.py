from src.models.repeatable_field import RepeatableFieldMapping
from src.models.repeatable_section import RepeatableSection

# Field mappings for basic information
BASIC_FIELDS = {
    "Family Name (Last Name)": "Pt1Line1a_FamilyName[0]",
    "Given Name (First Name)": "Pt1Line1b_GivenName[0]",
    "Middle Name": "Pt1Line1c_MiddleName[0]",
    "Street Number and Name": "Pt1Line12_StreetNumberName[0]",
    "City or Town": "Pt1Line12_CityOrTown[0]",
    "State": "Pt1Line12_State[0]",
    "ZIP Code": "Pt1Line12_ZipCode[0]"
}

# Address History Section
ADDRESS_SECTION = RepeatableSection(
    section_id="address_history",
    section_name="Address History",
    description="List of previous addresses",
    base_page_number=3,
    max_entries_per_page=4,
    field_mappings={
        "street": RepeatableFieldMapping(
            field_name="street",
            pdf_field_pattern="Pt3Line{index}_StreetNumberName[0]",
            field_type="text",
            max_entries=4,
            field_indices=[5, 7, 9, 11]
        ),
        "apt_number": RepeatableFieldMapping(
            field_name="apt_number",
            pdf_field_pattern="Pt3Line{index}_AptSteFlrNumber[0]",
            field_type="text",
            max_entries=4,
            field_indices=[5, 7, 9, 11]
        ),
        "city": RepeatableFieldMapping(
            field_name="city",
            pdf_field_pattern="Pt3Line{index}_CityOrTown[0]",
            field_type="text",
            max_entries=4,
            field_indices=[5, 7, 9, 11]
        ),
        "state": RepeatableFieldMapping(
            field_name="state",
            pdf_field_pattern="Pt3Line{index}_State[0]",
            field_type="text",
            max_entries=4,
            field_indices=[5, 7, 9, 11]
        ),
        "zip_code": RepeatableFieldMapping(
            field_name="zip_code",
            pdf_field_pattern="Pt3Line{index}_ZipCode[0]",
            field_type="text",
            max_entries=4,
            field_indices=[5, 7, 9, 11]
        ),
        "date_from": RepeatableFieldMapping(
            field_name="date_from",
            pdf_field_pattern="Pt3Line{index}_DateFrom[0]",
            field_type="date",
            max_entries=4,
            field_indices=[5, 7, 9, 11]
        ),
        "date_to": RepeatableFieldMapping(
            field_name="date_to",
            pdf_field_pattern="Pt3Line{index}_DateTo[0]",
            field_type="date",
            max_entries=4,
            field_indices=[5, 7, 9, 11]
        )
    }
)

# Employment History Section
EMPLOYMENT_SECTION = RepeatableSection(
    section_id="employment_history",
    section_name="Employment History",
    description="List of previous employment",
    base_page_number=3,
    max_entries_per_page=4,
    field_mappings={
        "employer": RepeatableFieldMapping(
            field_name="employer",
            pdf_field_pattern="Pt3Line{index}a_EmployerName[0]",
            field_type="text",
            max_entries=4,
            field_indices=[13, 15, 17, 19]
        ),
        "occupation": RepeatableFieldMapping(
            field_name="occupation",
            pdf_field_pattern="Pt3Line{index}a_OccupationTitle[0]",
            field_type="text",
            max_entries=4,
            field_indices=[13, 15, 17, 19]
        ),
        "date_from": RepeatableFieldMapping(
            field_name="date_from",
            pdf_field_pattern="Pt3Line{index}a_DateFrom[0]",
            field_type="date",
            max_entries=4,
            field_indices=[13, 15, 17, 19]
        ),
        "date_to": RepeatableFieldMapping(
            field_name="date_to",
            pdf_field_pattern="Pt3Line{index}a_DateTo[0]",
            field_type="date",
            max_entries=4,
            field_indices=[13, 15, 17, 19]
        )
    }
)

# Family Members Section
FAMILY_SECTION = RepeatableSection(
    section_id="family_members",
    section_name="Family Members",
    description="List of family members",
    base_page_number=4,
    max_entries_per_page=4,
    field_mappings={
        "relationship": RepeatableFieldMapping(
            field_name="relationship",
            pdf_field_pattern="Pt4Line{index}a_Relationship[0]",
            field_type="text",
            max_entries=4,
            field_indices=[1, 3, 5, 7]
        ),
        "family_name": RepeatableFieldMapping(
            field_name="family_name",
            pdf_field_pattern="Pt4Line{index}a_FamilyName[0]",
            field_type="text",
            max_entries=4,
            field_indices=[1, 3, 5, 7]
        ),
        "given_name": RepeatableFieldMapping(
            field_name="given_name",
            pdf_field_pattern="Pt4Line{index}a_GivenName[0]",
            field_type="text",
            max_entries=4,
            field_indices=[1, 3, 5, 7]
        ),
        "date_of_birth": RepeatableFieldMapping(
            field_name="date_of_birth",
            pdf_field_pattern="Pt4Line{index}a_DateOfBirth[0]",
            field_type="date",
            max_entries=4,
            field_indices=[1, 3, 5, 7]
        ),
        "country_of_birth": RepeatableFieldMapping(
            field_name="country_of_birth",
            pdf_field_pattern="Pt4Line{index}a_CountryOfBirth[0]",
            field_type="text",
            max_entries=4,
            field_indices=[1, 3, 5, 7]
        )
    }
)