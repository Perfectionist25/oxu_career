# from modeltranslation.translator import translator, TranslationOptions
# from .models import Company, EmployerProfile, Job, JobApplication, CandidateNote, Interview, CompanyReview

# class CompanyTranslationOptions(TranslationOptions):
#     fields = (
#         'name',
#         'description',
#         'headquarters',
#     )

# class EmployerProfileTranslationOptions(TranslationOptions):
#     fields = (
#         'professional_bio',
#         'job_title',
#     )

# class JobTranslationOptions(TranslationOptions):
#     fields = (
#         'title',
#         'description',
#         'requirements',
#         'responsibilities',
#         'benefits',
#         'location',
#         'skills_required',
#     )

# class JobApplicationTranslationOptions(TranslationOptions):
#     fields = ('cover_letter',)

# class CandidateNoteTranslationOptions(TranslationOptions):
#     fields = ('note',)

# class InterviewTranslationOptions(TranslationOptions):
#     fields = (
#         'location',
#         'notes',
#         'feedback',
#     )

# class CompanyReviewTranslationOptions(TranslationOptions):
#     fields = (
#         'title',
#         'review',
#         'pros',
#         'cons',
#     )

# translator.register(Company, CompanyTranslationOptions)
# # Do not register EmployerProfile translations yet — database columns for translated
# # fields (e.g. `job_title_<lang>`) are not present in the current schema.
# # translator.register(EmployerProfile, EmployerProfileTranslationOptions)
# translator.register(Job, JobTranslationOptions)
# translator.register(JobApplication, JobApplicationTranslationOptions)
# translator.register(CandidateNote, CandidateNoteTranslationOptions)
# translator.register(Interview, InterviewTranslationOptions)
# translator.register(CompanyReview, CompanyReviewTranslationOptions)
